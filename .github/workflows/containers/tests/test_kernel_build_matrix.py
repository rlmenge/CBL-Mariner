# ruff: noqa: INP001 — Tests for standalone workflow helpers.
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
"""Test matrix selection and failure on missing native build targets."""

from __future__ import annotations

import json
import runpy
import subprocess
from pathlib import Path

import pytest

eligible_jobs = runpy.run_path(str(Path(__file__).resolve().parents[1] / "kernel-build-matrix.py"))["eligible_jobs"]
PACKAGES = {"kernel": "kernel-core", "kernel-headers": "kernel-headers"}


def mock_query(monkeypatch: pytest.MonkeyPatch, *, excluded: bool = False) -> None:
    """Return the pinned azldev query shape for each target."""

    def query(args: list[str], *, text: bool) -> str:
        assert text
        arch = args[args.index("--arch") + 1]
        kernel = {"Name": "kernel", "Version": {"Version": "6.18"}, "Subpackages": ["kernel-core"]}
        headers = {"Name": "kernel-headers", "Version": {"Version": "6.18"}, "Subpackages": ["kernel-headers"]}
        return json.dumps([kernel, {"Name": "kernel-headers"} if excluded and arch == "aarch64" else headers])

    monkeypatch.setattr(subprocess, "check_output", query)


@pytest.mark.parametrize("full", [False, True])
def test_selects_native_matrix(monkeypatch: pytest.MonkeyPatch, *, full: bool) -> None:
    """Keep one native headers build per supported target, plus optional kernel builds."""
    mock_query(monkeypatch)
    jobs = eligible_jobs(PACKAGES, full=full)
    assert {(job["arch"], job["component"]) for job in jobs} == {
        (arch, component) for arch in ("x86_64", "aarch64") for component in (PACKAGES if full else ["kernel-headers"])
    }


def test_rejects_lost_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never publish a matrix that silently drops a required native build."""
    mock_query(monkeypatch, excluded=True)
    with pytest.raises(ValueError, match="aarch64: kernel-headers"):
        eligible_jobs(PACKAGES, full=True)


@pytest.mark.parametrize("kconfig_retry", [False, True])
def test_only_opted_in_kernel_jobs_retry(monkeypatch: pytest.MonkeyPatch, *, kconfig_retry: bool) -> None:
    """Opting in enables the existing Kconfig retry only for native kernel jobs."""
    mock_query(monkeypatch)
    jobs = eligible_jobs(PACKAGES, full=True, kconfig_retry=kconfig_retry)
    assert {(job["arch"], job["component"]) for job in jobs if job["kconfig_retry"]} == (
        {("x86_64", "kernel"), ("aarch64", "kernel")} if kconfig_retry else set()
    )
