# ruff: noqa: INP001
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Repair only unambiguous Kconfig removals or renames reported by RPM %prep."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tarfile
from http import HTTPStatus
from http.client import HTTPSConnection
from pathlib import Path

REPO = "microsoft/CBL-Mariner-Linux-Kernel"
SYMBOL = r"[A-Za-z0-9_]+"
MAX_SYMBOLS = 20
MAX_KCONFIG_BYTES = 2_000_000
SHA = re.compile(r"[0-9a-f]{40}")
DECLARATION = re.compile(rf"(?m)^[ \t]*(?:menu)?config[ \t]+({SYMBOL})[ \t]*$")
UNSUPPORTED = re.compile(rf"Unsupported CONFIG_({SYMBOL}) in .*/configs/kernel-[\d.]+-([a-z0-9_]+)\.config\.orig:\d+")
PREP_END = re.compile(r"^error: Bad exit status from .* \(%prep\)$", re.MULTILINE)
RTC_COMMIT = "2a56366a77b9eb8ade09ed8ef58eac122c6ca743"
RTC_DEPENDENCY = "\tdepends on ACPI_TAD || !ACPI_TAD"
RTC_MISMATCH = "Found CONFIG_RTC_DRV_EFI=m after generation, had CONFIG_RTC_DRV_EFI=y in Source tree"


def diagnose(log: str, arch: str) -> tuple[set[str], bool]:
    """Identify native unsupported symbols and the supported RTC mismatch."""
    starts = list(re.finditer(r"(?m)^\+ \./process_configs\.sh -w -n -c [\d.]+\s*$", log))
    if not starts or not (end := PREP_END.search(log, starts[-1].end())):
        raise ValueError("No matching process_configs.sh failure in RPM %prep")
    block = log[starts[-1].end() : end.start()]
    if re.search(r"Found (?:unset|misconfigured) config|Executing\(%build\)", block):
        raise ValueError("The failure needs a Kconfig policy decision")
    kconfig_arch = "arm64" if arch == "aarch64" else arch
    symbol_block, mismatch_header, mismatch = block.partition(
        f"Error: Mismatches found in configuration files for {kconfig_arch} {arch}\n"
    )
    rtc = bool(mismatch_header)
    if rtc and (arch != "aarch64" or mismatch.strip() != RTC_MISMATCH):
        raise ValueError("Unrecognized Kconfig mismatch; refusing to guess a fix")
    if "Mismatches found" in symbol_block:
        raise ValueError("Unexpected Kconfig mismatch header")
    header = re.search(rf"(?m)^Unknown Kconfig symbols in {kconfig_arch} {arch}:$", symbol_block)
    if header is None:
        if rtc and "Unsupported " not in symbol_block and "Unknown Kconfig symbols" not in symbol_block:
            return set(), True
        raise ValueError("No matching native unsupported-symbol report")
    matches = [UNSUPPORTED.fullmatch(line) for line in symbol_block[header.end() :].splitlines() if line.strip()]
    if not matches or any(match is None or match[2] != arch for match in matches):
        raise ValueError("No unambiguous native unsupported-symbol diagnostics")
    symbols = {match[1] for match in matches if match is not None}
    if len(symbols) > MAX_SYMBOLS:
        raise ValueError("Too many unsupported symbols for automatic repair")
    return symbols, rtc


def old_definition_paths(revision: str, symbols: set[str]) -> dict[str, str]:
    """Find canonical paths in the old endpoint, including files missed by compare limits."""
    paths: dict[str, str] = {}
    connection = HTTPSConnection("codeload.github.com", timeout=30)
    connection.request("GET", f"/{REPO}/tar.gz/{revision}")
    with connection.getresponse() as response:
        if response.status != HTTPStatus.OK:
            raise ValueError(f"Cannot read old source archive: HTTP {response.status}")
        with tarfile.open(fileobj=response, mode="r|gz") as archive:
            for member in archive:
                path = member.name.partition("/")[2]
                if not member.isfile() or not re.fullmatch(r"(?:[A-Za-z0-9_.-]+/)*Kconfig(?:\.[A-Za-z0-9_.-]+)?", path):
                    continue
                stream = archive.extractfile(member)
                if stream is None or member.size > MAX_KCONFIG_BYTES:
                    raise ValueError(f"Cannot inspect {path}")
                for symbol in set(DECLARATION.findall(stream.read().decode())) & symbols:
                    if symbol in paths:
                        raise ValueError(f"Multiple old definitions of CONFIG_{symbol}")
                    paths[symbol] = path
    if paths.keys() != symbols:
        raise ValueError(f"No old declaration for {sorted(symbols - paths.keys())}")
    return paths


def api(endpoint: str, *fields: str) -> str:
    """Make a bounded GET against the fixed upstream repository."""
    return subprocess.check_output(
        ["gh", "api", "-X", "GET", f"repos/{REPO}/{endpoint}", *fields], text=True, timeout=45
    )


def reachable(commit: str, revision: str) -> bool:
    """Check ancestry without assuming the two rolling tags share a linear history."""
    return commit == revision or (
        api(f"compare/{commit}...{revision}", "-f", "per_page=1", "--jq", ".status")
    ).strip() in {"ahead", "identical"}


def causal_change(symbol: str, path: str, old: str, target: str) -> tuple[str | None, str]:
    """Find a causal removal or same-hunk rename in the target source history."""
    content = api(f"contents/{path}", "-f", f"ref={target}", "-H", "Accept: application/vnd.github.raw+json")
    target_symbols = set(DECLARATION.findall(content))
    if symbol in target_symbols:
        raise ValueError(f"CONFIG_{symbol} still exists at the target")
    candidates = []
    history = json.loads(api("commits", "-f", f"sha={target}", "-f", f"path={path}", "-f", "per_page=30"))
    for item in history:
        commit = item["sha"]
        if not SHA.fullmatch(commit):
            raise ValueError("Invalid upstream history commit ID")
        files = json.loads(api(f"commits/{commit}", "--jq", ".files"))
        details = next((file.get("patch") for file in files if file["filename"] == path), None)
        if not details:
            continue
        old_decl = rf"^-[ \t]*(?:menu)?config[ \t]+{re.escape(symbol)}[ \t]*$"
        if not re.search(old_decl, details, re.MULTILINE):
            continue
        rename = re.search(old_decl + rf"\n\+[ \t]*(?:menu)?config[ \t]+({SYMBOL})[ \t]*$", details, re.MULTILINE)
        if not reachable(commit, target) or reachable(commit, old):
            continue
        if rename:
            if rename[1] not in target_symbols or "rename" not in item["commit"]["message"].lower():
                raise ValueError(f"Cannot verify replacement for CONFIG_{symbol}")
            candidates.append((rename[1], commit))
        else:
            candidates.append((None, commit))
        break  # Newest causal removal on this path.
    if not candidates:
        raise ValueError(f"No verified causal commit in bounded history for CONFIG_{symbol}")
    return candidates[0]


def repair_arm_rtc(text: str, old: str, target: str) -> tuple[str, str]:
    """Keep EFI RTC built in by satisfying the verified tristate dependency."""
    for setting in ("CONFIG_ACPI_TAD=m", "CONFIG_RTC_DRV_EFI=y", "CONFIG_RTC_HCTOSYS=y"):
        if text.splitlines().count(setting) != 1:
            raise ValueError(f"Unexpected starting value of {setting.split('=')[0]}")
    path = "drivers/rtc/Kconfig"
    blocks = []
    for revision in (old, target):
        kconfig = api(f"contents/{path}", "-f", f"ref={revision}", "-H", "Accept: application/vnd.github.raw+json")
        block = re.search(r"(?m)^config RTC_DRV_EFI\n(?:[ \t].*\n|\n)*", kconfig)
        if block is None:
            raise ValueError("Missing canonical RTC_DRV_EFI declaration")
        blocks.append(block[0].splitlines())
    if RTC_DEPENDENCY in blocks[0] or RTC_DEPENDENCY not in blocks[1] or not reachable(RTC_COMMIT, target):
        raise ValueError("Cannot verify the EFI RTC dependency at the pinned endpoints")
    updated = re.sub(r"(?m)^CONFIG_ACPI_TAD=m$", "CONFIG_ACPI_TAD=y", text)
    reason = (
        "- `CONFIG_ACPI_TAD=m` -> `CONFIG_ACPI_TAD=y` (arm64): the new tristate dependency caps "
        "`CONFIG_RTC_DRV_EFI` at `m` when TAD is modular. Building TAD in keeps EFI RTC "
        "configured as built-in for early clock initialization.\n"
        f"  https://github.com/{REPO}/commit/{RTC_COMMIT}"
    )
    return updated, reason


def repair(log: Path, config: Path, arch: str, old: str, target: str) -> str:
    """Apply validated changes together and return copyable justifications."""
    symbols, rtc = diagnose(log.read_text(errors="replace"), arch)
    paths = old_definition_paths(old, symbols) if symbols else {}
    text = config.read_text()
    notes = []
    for symbol in sorted(symbols):
        entry = re.compile(rf"(?m)^(?:# CONFIG_{symbol} is not set|CONFIG_{symbol}=([my]))$")
        matches = list(entry.finditer(text))
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one tristate entry for CONFIG_{symbol}")
        replacement, commit = causal_change(symbol, paths[symbol], old, target)
        value = matches[0][1]
        if replacement is None:
            if value:
                raise ValueError(f"Refusing to remove enabled CONFIG_{symbol} without a verified rename")
            start, end = matches[0].span()
            text = text[:start] + text[end + (text[end : end + 1] == "\n") :]
            reason = f"`CONFIG_{symbol}` (unset) -> removed ({arch}): upstream removed this disabled option."
        else:
            if not value or re.search(rf"(?m)^(?:# )?CONFIG_{replacement}(?:=| is not set$)", text):
                raise ValueError(f"Cannot preserve CONFIG_{symbol} state unambiguously")
            text = entry.sub(f"CONFIG_{replacement}={value}", text)
            mode = "module" if value == "m" else "built-in"
            reason = (
                f"`CONFIG_{symbol}={value}` -> `CONFIG_{replacement}={value}` ({arch}): "
                f"upstream renamed the symbol; preserves {mode} selection."
            )
        notes.append(f"- {reason}\n  https://github.com/{REPO}/commit/{commit}")
    if rtc:
        text, note = repair_arm_rtc(text, old, target)
        notes.append(note)
    config.write_text(text)
    return "\n".join(notes) + "\n"


def main() -> None:
    """Run the repair on the affected architecture's source config only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("arch", choices=("x86_64", "aarch64"))
    parser.add_argument("old")
    parser.add_argument("target")
    parser.add_argument("notes", type=Path)
    args = parser.parse_args()
    if not SHA.fullmatch(args.old) or not SHA.fullmatch(args.target):
        parser.error("Expected immutable upstream commit IDs")
    try:
        config = Path(f"base/comps/kernel/6.18-{args.arch}-azl.config")
        args.notes.write_text(repair(args.log, config, args.arch, args.old, args.target))
    except ValueError as exc:
        parser.exit(1, f"Kconfig retry refused: {exc}\n")


if __name__ == "__main__":
    main()
