#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Audit kernel config history against the required-config JSON.

The script walks commits that touched SPECS/kernel or SPECS/kernel-hwe config
files, extracts the config values introduced by each commit, and checks whether
the required-config JSON already covers the package/architecture/value.

By default this is read-only and prints a report. Pass --write to add missing
non-autoupdate entries to the JSON with commit and PR provenance.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CONFIG_PATHS = {
    "SPECS/kernel/config": ("kernel", "x86_64"),
    "SPECS/kernel/config_aarch64": ("kernel", "arm64"),
    "SPECS/kernel-hwe/config": ("kernel-hwe", "x86_64"),
    "SPECS/kernel-hwe/config_aarch64": ("kernel-hwe", "arm64"),
}

AUTOUPDATE_PATTERN = re.compile(
    r"(auto[- ]?(update|upgrade|patch|cherry)|autopatch|autoupgrade|"
    r"\bkernel[- ]upgrade\b|update kernel to|bump kernel)",
    re.IGNORECASE,
)
SOURCE_UPGRADE_PATTERN = re.compile(
    r"(match(es|ing)? .*(source|upstream|branch|kernel|config)|"
    r"(source|upstream|branch|kernel|config).* match(es|ing)?|"
    r"sync .*config|config .*sync|"
    r"converge .*config|config .*converge|"
    r"update .*config.*match|"
    r"upgrade .*config)",
    re.IGNORECASE,
)
PR_PATTERN = re.compile(r"#(\d+)")
CONFIG_SET_PATTERN = re.compile(r"^\+CONFIG_([A-Za-z0-9_]+)=(.*)$")
CONFIG_UNSET_PATTERN = re.compile(r"^\+# CONFIG_([A-Za-z0-9_]+) is not set$")
DERIVED_PREFIXES = (
    "CONFIG_ARCH_HAS_",
    "CONFIG_AS_",
    "CONFIG_CC_",
    "CONFIG_CLANG_",
    "CONFIG_GCC_",
    "CONFIG_HAVE_",
    "CONFIG_LD_",
    "CONFIG_LLD_",
    "CONFIG_PAHOLE_",
    "CONFIG_TOOLS_",
)
DERIVED_EXACT = {
    "CONFIG_BUILD_SALT",
    "CONFIG_BUILDTIME_TABLE_SORT",
    "CONFIG_INIT_ENV_ARG_LIMIT",
    "CONFIG_LOCALVERSION",
    "CONFIG_LOCALVERSION_AUTO",
    "CONFIG_THREAD_INFO_IN_TASK",
}
HELPER_SUFFIXES = (
    "_ARCH",
    "_CMDLINE",
    "_COMPRESS",
    "_DECOMPRESS",
    "_GENERIC",
    "_INTERNAL",
    "_RSIZE",
    "_STATS",
    "_TESTINTERFACE",
)


@dataclass(frozen=True)
class ConfigChange:
    commit: str
    short_commit: str
    subject: str
    path: str
    package: str
    arch: str
    symbol: str
    value: str
    is_autoupdate: bool
    prs: tuple[str, ...]


def run_git(repo: Path, args: list[str]) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def is_git_commit(repo: Path, value: str) -> bool:
    try:
        subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "--verify", f"{value}^{{commit}}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def iter_commits(repo: Path, since: str | None, until: str) -> Iterable[str]:
    args = ["log", "--format=%H"]
    if since:
        if is_git_commit(repo, since):
            args.append(f"{since}..{until}")
        else:
            args.extend([f"--since={since}", until])
    else:
        args.append(until)
    args.extend(["--", *CONFIG_PATHS])
    output = run_git(repo, args)
    for line in output.splitlines():
        if line:
            yield line


def parse_added_config(line: str) -> tuple[str, str] | None:
    set_match = CONFIG_SET_PATTERN.match(line)
    if set_match:
        return f"CONFIG_{set_match.group(1)}", set_match.group(2)

    unset_match = CONFIG_UNSET_PATTERN.match(line)
    if unset_match:
        return f"CONFIG_{unset_match.group(1)}", "n"

    return None


def commit_changes(
    repo: Path,
    commit: str,
    include_autoupdate_details: bool,
    skip_source_upgrade: bool,
    max_changes_per_commit: int,
) -> tuple[list[ConfigChange], str | None]:
    subject = run_git(repo, ["show", "-s", "--format=%s", commit]).strip()
    is_autoupdate = AUTOUPDATE_PATTERN.search(subject) is not None
    is_source_upgrade = SOURCE_UPGRADE_PATTERN.search(subject) is not None
    prs = tuple(PR_PATTERN.findall(subject))
    short_commit = commit[:12]
    changes: list[ConfigChange] = []

    if is_autoupdate and not include_autoupdate_details:
        return changes, "autoupdate_commit_skipped"
    if skip_source_upgrade and is_source_upgrade:
        return changes, "source_upgrade_commit_skipped"

    for path, (package, arch) in CONFIG_PATHS.items():
        diff = run_git(repo, ["show", "--format=", "--unified=0", commit, "--", path])
        seen_in_commit: dict[str, str] = {}
        for line in diff.splitlines():
            parsed = parse_added_config(line)
            if parsed is None:
                continue
            symbol, value = parsed
            seen_in_commit[symbol] = value

        for symbol, value in seen_in_commit.items():
            changes.append(
                ConfigChange(
                    commit=commit,
                    short_commit=short_commit,
                    subject=subject,
                    path=path,
                    package=package,
                    arch=arch,
                    symbol=symbol,
                    value=value,
                    is_autoupdate=is_autoupdate,
                    prs=prs,
                )
            )

    if len(changes) > max_changes_per_commit:
        return [], "large_config_commit_skipped"

    return changes, None


def load_json(path: Path) -> OrderedDict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=OrderedDict)


def section_configs(data: dict, section_name: str | None) -> list[dict]:
    if section_name is None:
        return data["default"]["kernel_configs"]

    for override in data.get("overrides", []):
        if override.get("name") == section_name:
            return override["kernel_configs"]

    overrides = data.setdefault("overrides", [])
    new_override = OrderedDict([("name", section_name), ("kernel_configs", [])])
    overrides.append(new_override)
    return new_override["kernel_configs"]


def entry_value(entry: dict, arch: str) -> str | None:
    for item in entry.get("values", []):
        if item.get("architecture") == arch:
            return item.get("value")
    return None


def find_entry(configs: list[dict], symbol: str) -> dict | None:
    for entry in configs:
        if entry.get("name") == symbol:
            return entry
    return None


def effective_value(data: dict, package: str, arch: str, symbol: str) -> str | None:
    default_entry = find_entry(data["default"]["kernel_configs"], symbol)
    value = entry_value(default_entry, arch) if default_entry else None

    override_entry = find_entry(section_configs(data, package), symbol)
    override_value = entry_value(override_entry, arch) if override_entry else None
    return override_value if override_value is not None else value


def target_section(data: dict, change: ConfigChange) -> str | None:
    if change.package == "kernel":
        return None

    default_entry = find_entry(data["default"]["kernel_configs"], change.symbol)
    default_value = entry_value(default_entry, change.arch) if default_entry else None
    if default_value == change.value:
        return None

    return change.package


def add_missing_entry(data: dict, change: ConfigChange) -> None:
    section_name = target_section(data, change)
    configs = section_configs(data, section_name)
    entry = find_entry(configs, change.symbol)
    if entry is None:
        entry = OrderedDict(
            [
                ("name", change.symbol),
                ("values", []),
                ("justification", justification_for(change)),
            ]
        )
        configs.append(entry)

    for item in entry["values"]:
        if item.get("architecture") == change.arch:
            item["value"] = change.value
            break
    else:
        entry["values"].append(
            OrderedDict([("architecture", change.arch), ("value", change.value)])
        )

    if not entry.get("justification"):
        entry["justification"] = justification_for(change)


def justification_for(change: ConfigChange) -> str:
    pr_text = ""
    if change.prs:
        pr_links = ", ".join(
            f"https://github.com/microsoft/azurelinux/pull/{pr}" for pr in change.prs
        )
        pr_text = f" PR: {pr_links}."
    return (
        f"Tracked from {change.package} {change.arch} config change in commit "
        f"{change.commit}.{pr_text} Subject: {change.subject}"
    )


def classify_change(data: dict, change: ConfigChange) -> str:
    existing = effective_value(data, change.package, change.arch, change.symbol)
    if existing == change.value:
        return "covered"
    if existing is not None:
        return "json_value_diff"
    if change.is_autoupdate:
        return "autoupdate_missing_warning"
    return "missing"


def is_critical_candidate(change: ConfigChange) -> bool:
    """Return whether a config is likely a policy root instead of generated chaff.

    This intentionally keeps the filter conservative:
    - disabled values are usually dependency/default fallout and are skipped;
    - compiler/toolchain/capability symbols are generated by Kconfig;
    - common library helper suffixes are usually selected by root features.
    """

    if change.value == "n":
        return False
    if change.symbol in DERIVED_EXACT:
        return False
    if change.symbol.startswith(DERIVED_PREFIXES):
        return False
    if change.symbol.endswith(HELPER_SUFFIXES):
        return False
    return True


def write_report(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit kernel config commits against required config JSON"
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root to audit (default: current directory)",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path(
            "toolkit/scripts/kernel_config_checker/kernel_configs_json/"
            "azl3-os-required-kernel-configs.json"
        ),
        help="Required kernel config JSON path",
    )
    parser.add_argument(
        "--since",
        help="Oldest commit/ref to exclude, e.g. 2023-01-01 or a commit SHA",
    )
    parser.add_argument(
        "--until",
        default="HEAD",
        help="Newest commit/ref to include (default: HEAD)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Update the JSON with missing non-autoupdate entries",
    )
    parser.add_argument(
        "--critical-only",
        action="store_true",
        help=(
            "Only report/write likely root policy symbols; skip disabled values, "
            "toolchain/generated symbols, and common selected helper dependencies"
        ),
    )
    parser.add_argument(
        "--skip-source-upgrade-commits",
        action="store_true",
        help=(
            "Skip commits whose subject indicates config churn from matching, "
            "syncing, converging, or upgrading source configs"
        ),
    )
    parser.add_argument(
        "--include-autoupdate-details",
        action="store_true",
        help=(
            "Parse auto-update commits in detail instead of emitting one skipped "
            "warning per auto-update commit"
        ),
    )
    parser.add_argument(
        "--max-changes-per-commit",
        type=int,
        default=200,
        help=(
            "Skip commits with more than this many added config values as bulk "
            "config imports/upgrades (default: 200)"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional CSV report path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    json_path = args.json if args.json.is_absolute() else repo / args.json
    data = load_json(json_path)

    rows: list[dict] = []
    counts: dict[str, int] = {}
    for commit in iter_commits(repo, args.since, args.until):
        changes, skipped_status = commit_changes(
            repo,
            commit,
            args.include_autoupdate_details,
            args.skip_source_upgrade_commits,
            args.max_changes_per_commit,
        )
        if skipped_status:
            subject = run_git(repo, ["show", "-s", "--format=%s", commit]).strip()
            counts[skipped_status] = counts.get(skipped_status, 0) + 1
            rows.append(
                {
                    "status": skipped_status,
                    "package": "",
                    "arch": "",
                    "symbol": "",
                    "value": "",
                    "commit": commit,
                    "subject": subject,
                    "path": "",
                    "prs": ";".join(PR_PATTERN.findall(subject)),
                }
            )
            continue

        for change in changes:
            status = classify_change(data, change)
            if status == "missing" and args.critical_only and not is_critical_candidate(change):
                status = "dependency_or_generated_skipped"
            if args.write and status == "missing":
                add_missing_entry(data, change)
                status = "added"
            counts[status] = counts.get(status, 0) + 1

            rows.append(
                {
                    "status": status,
                    "package": change.package,
                    "arch": change.arch,
                    "symbol": change.symbol,
                    "value": change.value,
                    "commit": change.commit,
                    "subject": change.subject,
                    "path": change.path,
                    "prs": ";".join(change.prs),
                }
            )

    if args.write:
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")

    if args.report and rows:
        write_report(args.report, rows)

    print("summary")
    for status in sorted(counts):
        print(f"{status}: {counts[status]}")

    missing_like = [
        row
        for row in rows
        if row["status"]
        in {
            "missing",
            "autoupdate_missing_warning",
            "autoupdate_commit_skipped",
            "large_config_commit_skipped",
            "source_upgrade_commit_skipped",
            "json_value_diff",
        }
    ]
    for row in missing_like[:100]:
        if row["status"] in {
            "autoupdate_commit_skipped",
            "large_config_commit_skipped",
            "source_upgrade_commit_skipped",
        }:
            print(
                "{status}: commit={commit} {subject}".format(
                    **row
                )
            )
        else:
            print(
                "{status}: {package}/{arch} {symbol}={value} commit={commit} {subject}".format(
                    **row
                )
            )
    if len(missing_like) > 100:
        print(f"... {len(missing_like) - 100} more rows")

    return 0


if __name__ == "__main__":
    sys.exit(main())
