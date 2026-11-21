# ruff: noqa: INP001
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Propose bounded repairs for native Kconfig failures reported by RPM %prep."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tarfile
from http import HTTPStatus
from http.client import HTTPSConnection
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Iterator

REPO = "microsoft/CBL-Mariner-Linux-Kernel"
SYMBOL = r"[A-Za-z0-9_]+"
MAX_SYMBOLS = 20
MAX_KCONFIG_BYTES = 2_000_000
SHA = re.compile(r"[0-9a-f]{40}")
DECLARATION = re.compile(rf"(?m)^[ \t]*(?:menu)?config[ \t]+({SYMBOL})[ \t]*$")
UNSUPPORTED = re.compile(rf"Unsupported CONFIG_({SYMBOL}) in .*/configs/kernel-[\d.]+-([a-z0-9_]+)\.config\.orig:\d+")
PREP_END = re.compile(r"^error: Bad exit status from .* \(%prep\)$", re.MULTILINE)
VALUE_MISMATCH = re.compile(
    rf"Found CONFIG_({SYMBOL})=([ym]) after generation, had CONFIG_\1=(y|m|is not set) in Source tree"
)
UNSET_MISMATCH = re.compile(
    rf"Found # CONFIG_({SYMBOL}) is not set, after generation, had CONFIG_\1 ([ym]) in Source tree"
)
MODULE_GATE = re.compile(rf"depends on ({SYMBOL}) \|\| !\1")


class Source(NamedTuple):
    """Location of a diagnosed symbol across the two kernel sources."""

    path: str
    old: str
    target: str


def mismatch_values(report: str) -> dict[str, tuple[str, str]]:
    """Parse exact, distinct generated/requested value pairs."""
    values = {}
    for line in report.strip().splitlines():
        if match := VALUE_MISMATCH.fullmatch(line):
            symbol, generated, requested = match.groups()
        elif match := UNSET_MISMATCH.fullmatch(line):
            symbol, requested = match.groups()
            generated = "is not set"
        else:
            raise ValueError("Unrecognized Kconfig mismatch; refusing to guess a fix")
        if symbol in values or generated == requested:
            raise ValueError("Unrecognized Kconfig mismatch; refusing to guess a fix")
        values[symbol] = (requested, generated)
    if not values or len(values) > MAX_SYMBOLS:
        raise ValueError("Missing or too many Kconfig mismatch diagnostics")
    return values


def diagnose(log: str, arch: str) -> tuple[set[str], dict[str, tuple[str, str]]]:
    """Identify native unsupported symbols and tristate mismatches."""
    starts = list(re.finditer(r"(?m)^\+ \./process_configs\.sh -w -n -c [\d.]+\s*$", log))
    if not starts or not (end := PREP_END.search(log, starts[-1].end())):
        raise ValueError("No matching process_configs.sh failure in RPM %prep")
    block = log[starts[-1].end() : end.start()]
    # Hosted RPM can print its warning heading before, rather than after, the %prep error.
    block = re.sub(r"(?m)^RPM build warnings:[ \t]*\n[ \t\n]*\Z", "", block)
    if re.search(r"Found (?:unset|misconfigured) config|Executing\(%build\)", block):
        raise ValueError("The failure needs a Kconfig policy decision")
    kconfig_arch = "arm64" if arch == "aarch64" else arch
    symbol_block, mismatch_header, mismatch = block.partition(
        f"Error: Mismatches found in configuration files for {kconfig_arch} {arch}\n"
    )
    values = mismatch_values(mismatch) if mismatch_header else {}
    if "Mismatches found" in symbol_block:
        raise ValueError("Unexpected Kconfig mismatch header")
    header = re.search(rf"(?m)^Unknown Kconfig symbols in {kconfig_arch} {arch}:$", symbol_block)
    if header is None:
        if values and "Unsupported " not in symbol_block and "Unknown Kconfig symbols" not in symbol_block:
            return set(), values
        raise ValueError("No matching native unsupported-symbol report")
    matches = [UNSUPPORTED.fullmatch(line) for line in symbol_block[header.end() :].splitlines() if line.strip()]
    if not matches or any(match is None or match[2] != arch for match in matches):
        raise ValueError("No unambiguous native unsupported-symbol diagnostics")
    symbols = {match[1] for match in matches if match is not None}
    if len(symbols) + len(values) > MAX_SYMBOLS or symbols.intersection(values):
        raise ValueError("Too many or conflicting Kconfig diagnostics for automatic repair")
    return symbols, values


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


def path_patches(path: str, target: str) -> Iterator[tuple[str, str, str]]:
    """Yield available patches from a bounded search of target path history."""
    history = json.loads(api("commits", "-f", f"sha={target}", "-f", f"path={path}", "-f", "per_page=30"))
    for item in history:
        commit = item["sha"]
        if not SHA.fullmatch(commit):
            raise ValueError("Invalid upstream history commit ID")
        files = json.loads(api(f"commits/{commit}", "--jq", ".files"))
        details = next((file.get("patch") for file in files if file["filename"] == path), None)
        if details:
            yield commit, item["commit"]["message"], details


def source_content(path: str, revision: str) -> str:
    """Read a canonical source file at an immutable endpoint."""
    return api(f"contents/{path}", "-f", f"ref={revision}", "-H", "Accept: application/vnd.github.raw+json")


def causal_change(symbol: str, path: str, old: str, target: str) -> tuple[str | None, str]:
    """Find a causal removal or same-hunk rename in the target source history."""
    target_symbols = set(DECLARATION.findall(source_content(path, target)))
    if symbol in target_symbols:
        raise ValueError(f"CONFIG_{symbol} still exists at the target")
    for commit, message, details in path_patches(path, target):
        old_decl = rf"^-[ \t]*(?:menu)?config[ \t]+{re.escape(symbol)}[ \t]*$"
        if not re.search(old_decl, details, re.MULTILINE):
            continue
        rename = re.search(old_decl + rf"\n\+[ \t]*(?:menu)?config[ \t]+({SYMBOL})[ \t]*$", details, re.MULTILINE)
        if not reachable(commit, target) or reachable(commit, old):
            continue
        if rename:
            if rename[1] not in target_symbols or "rename" not in message.lower():
                raise ValueError(f"Cannot verify replacement for CONFIG_{symbol}")
            return rename[1], commit
        return None, commit
    raise ValueError(f"No verified causal commit in bounded history for CONFIG_{symbol}")


def definition(content: str, symbol: str) -> set[str]:
    """Read the direct properties of a unique Kconfig declaration."""
    blocks = re.findall(rf"(?m)^(?:menu)?config {symbol}[ \t]*\n((?:[ \t]+[^\n]*\n|\n)*)", content)
    if len(blocks) != 1:
        raise ValueError(f"Missing or ambiguous canonical CONFIG_{symbol} declaration")
    return {line.strip() for line in blocks[0].splitlines()}


def config_line(symbol: str, value: str) -> str:
    """Render a tristate assignment in the distro config."""
    return f"# CONFIG_{symbol} is not set" if value == "is not set" else f"CONFIG_{symbol}={value}"


def repair_mismatch(text: str, symbol: str, values: tuple[str, str], arch: str, source: Source) -> tuple[str, str]:
    """Prefer keeping the requested mode by satisfying a newly added module gate."""
    path, old, target = source
    requested, generated = values
    before = config_line(symbol, requested)
    if text.splitlines().count(before) != 1:
        raise ValueError(f"Unexpected starting value of CONFIG_{symbol}")
    old_props = definition(source_content(path, old), symbol)
    target_content = source_content(path, target)
    new_props = definition(target_content, symbol)
    changed = {line for line in new_props - old_props if line.startswith(("depends on ", "def_tristate ", "default "))}
    # Only attribute a line to this declaration if it is unique in the target file.
    changed = {line for line in changed if sum(row.strip() == line for row in target_content.splitlines()) == 1}
    commit_url = ""
    gate = None
    if changed:
        for commit, _, patch in path_patches(path, target):
            added = {line[1:].strip() for line in patch.splitlines() if line.startswith("+")}
            if not (evidence := added & changed) or not reachable(commit, target) or reachable(commit, old):
                continue
            commit_url = f"\n  https://github.com/{REPO}/commit/{commit}"
            gates = [match[1] for line in evidence if (match := MODULE_GATE.fullmatch(line))]
            if len(gates) == 1 and gates[0] != symbol and (requested, generated) == ("y", "m"):
                gate = gates[0]
            break
    if gate and text.splitlines().count(f"CONFIG_{gate}=m") == 1:
        before, after = f"CONFIG_{gate}=m", f"CONFIG_{gate}=y"
        reason = f"tries to keep `CONFIG_{symbol}=y` by satisfying its new tristate dependency"
    else:
        after = config_line(symbol, generated)
        reason = "uses the value observed after Kconfig generation; the preferred runtime policy is not known"
    if not commit_url:
        reason += (
            "; no causal commit verified in bounded history "
            f"([old source](https://github.com/{REPO}/blob/{old}/{path}), "
            f"[new source](https://github.com/{REPO}/blob/{target}/{path}))"
        )
    note = f"- **Needs maintainer review:** `{before}` -> `{after}` ({arch}): {reason}.{commit_url}"
    return re.sub(rf"(?m)^{re.escape(before)}$", after, text), note


def repair(log: Path, config: Path, arch: str, old: str, target: str) -> str:
    """Apply validated changes together and return copyable justifications."""
    symbols, mismatches = diagnose(log.read_text(errors="replace"), arch)
    paths = old_definition_paths(old, symbols | mismatches.keys())
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
    for symbol, values in sorted(mismatches.items()):
        text, note = repair_mismatch(text, symbol, values, arch, Source(paths[symbol], old, target))
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
