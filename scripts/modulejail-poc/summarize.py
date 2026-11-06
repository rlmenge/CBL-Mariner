#!/usr/bin/env python3
"""Verify downloaded evidence and qualify the bounded AZL4 POC."""

import argparse
import hashlib
import json
from pathlib import Path
import tarfile


def ssh_checks(results, state, final_boot_id):
    latest = {}
    for path in sorted(results.glob("ssh-*.json")):
        record = json.loads(path.read_text(encoding="utf-8-sig"))
        if record.get("phase"):
            latest[record["phase"]] = record
    checks = {}
    for phase in ("enforce", "boot", "rollback"):
        record = latest.get(phase)
        if record is None:
            checks[phase] = False
            continue
        expected_policy = "absent" if phase == "rollback" else "present"
        expected_boot_id = state["enforced_boot_id"] if phase == "enforce" else final_boot_id
        checks[phase] = (
            record["passed"] and record["exit_code"] == 0
            and f"POLICY={expected_policy}" in record["output"]
            and state["upgrade_target"] in record["output"]
            and expected_boot_id in record["output"]
            and "EXTERNAL_SSH_PASS" in record["output"]
        )
    return checks


def summarize(results):
    archive_path = results / "evidence.tar.gz"
    actual = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    expected = (results / "evidence.sha256").read_text(encoding="utf-8-sig").strip()
    if actual != expected:
        raise RuntimeError("Downloaded evidence does not match the recorded remote SHA256.")
    destination = results / "evidence"
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination, filter="data")
    root = destination / "modulejail-poc"
    identity = json.loads((root / "guest-identity.json").read_text())
    state = json.loads((root / "state.json").read_text())
    target = state.get("upgrade_target")
    if not target:
        raise RuntimeError("Kernel-update qualification is incomplete; no upgrade target.")
    boot = json.loads((root / f"boot-{target}-workload.json").read_text())
    flags = (
        "prepared", "audited", "enforced", "boot_verified", "upgrade_boot_verified",
        "rollback_verified", "upgrade_policy_compared",
    )
    checks = {name: state.get(name) is True for name in flags}
    checks["guest_verdict"] = state.get("guest_verdict") == "PASS" and not state.get("last_error")
    checks["new_boot"] = boot["boot_id"] != state["enforced_boot_id"]
    checks["exact_kernel"] = boot["kernel"] == target
    for label in ("baseline", "audit", "enforce", "boot-" + state["initial_kernel"],
                  "boot-" + target, "rollback"):
        data = json.loads((root / f"{label}-workload.json").read_text())
        checks[label + "_workload"] = all(
            data[field] == "PASS" for field in ("https", "imds", "filesystem_io", "nft_rule_lifecycle")
        )
    external = ssh_checks(results, state, boot["boot_id"])
    checks.update({"external_ssh_" + phase: passed for phase, passed in external.items()})
    policy_diff = json.loads((root / "upgrade-policy-diff.json").read_text())
    result = {
        "verdict": "PASS" if all(checks.values()) else "INCOMPLETE",
        "scope": "Disposable x64 Azure Linux 4 basic-server ModuleJail 1.6.3 POC",
        "checks": checks, "initial_kernel": state["initial_kernel"], "upgrade_kernel": target,
        "probe": state["probe"], "candidate_modules": state["candidate_modules"],
        "resource_group": identity["resourceGroupName"],
        "evidence_sha256": actual, "upgrade_policy_diff": policy_diff,
        "limitations": [
            "One x64 VM and one kernel release transition; no ARM64, containers, network filesystems, GPU or SR-IOV qualification.",
            "Firewall testing covers a separate accept-only nftables table and rule lifecycle, not every firewall workload.",
            "AF_ALG interfaces are built in on this image; modprobe policy cannot disable them.",
            "External SSH must be recorded under enforcement, reboot and rollback; guest-only success is insufficient.",
            "Policy membership is frozen from a real module snapshot using upstream's fixture interface; regeneration after audit cannot silently grandfather new loads.",
            "Regenerated policy was compared but not applied; new module names require review after updates.",
        ],
    }
    (results / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    result = summarize(args.results)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["verdict"] == "PASS" else 1)
