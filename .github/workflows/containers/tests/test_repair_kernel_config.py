# ruff: noqa: INP001
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Regression tests for Kconfig diagnostics in hosted RPM build logs."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

helper = runpy.run_path(str(Path(__file__).resolve().parents[1] / "repair-kernel-config.py"))
diagnose = helper["diagnose"]
repair_mismatch = helper["repair_mismatch"]

X86_REPORT = """\
Unknown Kconfig symbols in x86_64 x86_64:
Unsupported CONFIG_SATA_INIC162X in /build/configs/kernel-6.18.64-x86_64.config.orig:2826
Unsupported CONFIG_LENOVO_WMI_DATA01 in /build/configs/kernel-6.18.64-x86_64.config.orig:6835
"""
ARM_REPORT = """\
Unknown Kconfig symbols in arm64 aarch64:
Unsupported CONFIG_SATA_INIC162X in /build/configs/kernel-6.18.64-aarch64.config.orig:3213
Error: Mismatches found in configuration files for arm64 aarch64
Found CONFIG_RTC_DRV_EFI=m after generation, had CONFIG_RTC_DRV_EFI=y in Source tree
"""


def prep_log(report: str, footer: str = "RPM build warnings:\n") -> str:
    """Build a minimal log with the RPM footer ordering used on hosted runners."""
    return (
        f"+ ./process_configs.sh -w -n -c 6.18.64\n{report}{footer}"
        "error: Bad exit status from /var/tmp/rpm-tmp.test (%prep)\n"
    )


@pytest.mark.parametrize("footer", ["", "RPM build warnings:\n"])
def test_x86_unsupported_symbols(footer: str) -> None:
    """Recognize both the local and hosted log formats."""
    assert diagnose(prep_log(X86_REPORT, footer), "x86_64") == ({"SATA_INIC162X", "LENOVO_WMI_DATA01"}, {})


def test_arm_removal_and_rtc_mismatch() -> None:
    """Recognize both diagnostics in the same arm64 failure."""
    assert diagnose(prep_log(ARM_REPORT), "aarch64") == ({"SATA_INIC162X"}, {"RTC_DRV_EFI": ("y", "m")})


@pytest.mark.parametrize(
    ("report", "footer"),
    [
        (ARM_REPORT.replace("RTC_DRV_EFI=y", "OTHER=y"), "RPM build warnings:\n"),
        (ARM_REPORT, "Unexpected diagnostic\nRPM build warnings:\n"),
        (ARM_REPORT, "RPM build warnings:\nUnexpected diagnostic\n"),
    ],
)
def test_other_diagnostics_still_block_retry(report: str, footer: str) -> None:
    """Do not discard real diagnostics around the warning heading."""
    with pytest.raises(ValueError, match="Unrecognized Kconfig mismatch"):
        diagnose(prep_log(report, footer), "aarch64")


def test_new_symbols_and_multiple_mismatches() -> None:
    """Diagnose new symbols without an architecture-specific allowlist."""
    report = (
        "Error: Mismatches found in configuration files for x86_64 x86_64\n"
        "Found CONFIG_EXAMPLE=m after generation, had CONFIG_EXAMPLE=y in Source tree\n"
        "Found CONFIG_OTHER=y after generation, had CONFIG_OTHER=m in Source tree\n"
        "Found # CONFIG_DISABLED is not set, after generation, had CONFIG_DISABLED y in Source tree\n"
        "Found CONFIG_ENABLED=y after generation, had CONFIG_ENABLED=is not set in Source tree\n"
    )
    assert diagnose(prep_log(report), "x86_64") == (
        set(),
        {"EXAMPLE": ("y", "m"), "OTHER": ("m", "y"), "DISABLED": ("y", "is not set"), "ENABLED": ("is not set", "y")},
    )


@pytest.mark.parametrize("verify_commit", [True, False])
def test_new_module_gate_proposal(monkeypatch: pytest.MonkeyPatch, *, verify_commit: bool) -> None:
    """Prefer a verified gate change; flag the observed-value fallback otherwise."""
    old = 'config EXAMPLE\n\ttristate "Example"\n'
    target = old + "\tdepends on SUPPORT || !SUPPORT\n"
    commit = "a" * 40
    scope = repair_mismatch.__globals__
    monkeypatch.setitem(scope, "source_content", lambda _path, ref: old if ref == "old" else target)
    monkeypatch.setitem(
        scope, "path_patches", lambda _path, _ref: iter([(commit, "new gate", "+\tdepends on SUPPORT || !SUPPORT")])
    )
    monkeypatch.setitem(scope, "reachable", lambda _sha, ref: verify_commit and ref == "new")
    config, note = repair_mismatch(
        "CONFIG_EXAMPLE=y\nCONFIG_SUPPORT=m\n",
        "EXAMPLE",
        ("y", "m"),
        "x86_64",
        helper["Source"]("Kconfig", "old", "new"),
    )
    assert "Needs maintainer review" in note
    if verify_commit:
        assert config == "CONFIG_EXAMPLE=y\nCONFIG_SUPPORT=y\n"
        assert f"/commit/{commit}" in note
    else:
        assert config == "CONFIG_EXAMPLE=m\nCONFIG_SUPPORT=m\n"
        assert "no causal commit verified" in note
