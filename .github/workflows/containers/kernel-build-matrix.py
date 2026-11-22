# ruff: noqa: INP001 — Standalone workflow helper.
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Resolve the kernel pilot's native build jobs from rendered RPM specs."""

from __future__ import annotations

import argparse
import json
import subprocess
import tomllib
from pathlib import Path

RUNNERS = {"x86_64": "ubuntu-24.04", "aarch64": "ubuntu-24.04-arm"}
RECIPE = Path("base/comps/kernel/update.toml")
COMPONENTS = ("kernel", "kernel-headers")


def eligible_jobs(packages: dict[str, str], *, full: bool, kconfig_retry: bool = False) -> list[dict[str, str | bool]]:
    """Verify both native targets remain available and expose the selected jobs."""
    jobs = []
    selectors = [arg for component in COMPONENTS for arg in ("-p", component)]
    for arch, runner in RUNNERS.items():
        output = subprocess.check_output(
            ["azldev", "comp", "query", "-q", "-O", "json", "--arch", arch, *selectors], text=True
        )
        rows = json.loads(output)
        by_name = {row["Name"]: row for row in rows}
        if set(by_name) != set(COMPONENTS) or len(rows) != len(COMPONENTS):
            raise ValueError(f"{arch}: incomplete or ambiguous component query")
        for component in COMPONENTS:
            result = by_name[component]
            if not result.get("Version") or packages[component] not in (result.get("Subpackages") or []):
                raise ValueError(
                    f"{arch}: {component} no longer reports {packages[component]}; maintainer review required"
                )
            if full or component == "kernel-headers":
                jobs.append(
                    {
                        "component": component,
                        "arch": arch,
                        "runner": runner,
                        "binary": packages[component],
                        "kconfig_retry": kconfig_retry and component == "kernel",
                    }
                )
    return jobs


def main() -> None:
    """Emit checked jobs as a GitHub Actions include matrix."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("full", choices=("true", "false"))
    args = parser.parse_args()
    recipe = tomllib.loads(RECIPE.read_text())
    packages = recipe["build"]
    if packages != {"kernel": "kernel-core", "kernel-headers": "kernel-headers"}:
        parser.error("Unexpected kernel build recipe; expected the native kernel-core and kernel-headers binary RPMs")
    retry = recipe.get("retry", {})
    if not isinstance(retry, dict) or retry.keys() - {"kconfig"}:
        parser.error("Expected an optional [retry] table with a kconfig setting")
    kconfig_retry = retry.get("kconfig", False)
    if not isinstance(kconfig_retry, bool):
        parser.error("Expected retry.kconfig to be a boolean")
    jobs = eligible_jobs(packages, full=args.full == "true", kconfig_retry=kconfig_retry)
    print(json.dumps(jobs, separators=(",", ":")))


if __name__ == "__main__":
    main()
