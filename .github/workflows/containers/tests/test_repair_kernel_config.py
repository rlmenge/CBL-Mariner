# ruff: noqa: INP001
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Regression tests for Kconfig diagnostics in hosted RPM build logs."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

diagnose = runpy.run_path(str(Path(__file__).resolve().parents[1] / "repair-kernel-config.py"))["diagnose"]

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
    assert diagnose(prep_log(X86_REPORT, footer), "x86_64") == ({"SATA_INIC162X", "LENOVO_WMI_DATA01"}, False)


def test_arm_removal_and_rtc_mismatch() -> None:
    """Recognize both diagnostics in the same arm64 failure."""
    assert diagnose(prep_log(ARM_REPORT), "aarch64") == ({"SATA_INIC162X"}, True)


@pytest.mark.parametrize(
    ("report", "footer"),
    [
        (ARM_REPORT.replace("RTC_DRV_EFI", "OTHER"), "RPM build warnings:\n"),
        (ARM_REPORT, "Unexpected diagnostic\nRPM build warnings:\n"),
        (ARM_REPORT, "RPM build warnings:\nUnexpected diagnostic\n"),
    ],
)
def test_other_diagnostics_still_block_retry(report: str, footer: str) -> None:
    """Do not discard real diagnostics around the warning heading."""
    with pytest.raises(ValueError, match="Unrecognized Kconfig mismatch"):
        diagnose(prep_log(report, footer), "aarch64")
