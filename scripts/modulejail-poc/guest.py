#!/usr/bin/env python3
"""Bounded ModuleJail experiment for the dedicated disposable AZL4 guest."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import urllib.request


ROOT = Path("/var/lib/modulejail-poc")
POLICY = Path("/etc/modprobe.d/modulejail-blacklist.conf")
HOOK = Path("/usr/lib/dracut/modules.d/99modulejail-strip/module-setup.sh")
FINGERPRINT = "095F5C8B39AF010E7B615CD4487BC00D69C2A955"
COMMIT = "ebbdde87503d39546375e308b3c1f298d6c8ab17"
TOOL = ROOT / "source/modulejail"
STATE = ROOT / "state.json"
PROBES = {
    "algif_hash": "s=socket.socket(socket.AF_ALG,socket.SOCK_SEQPACKET);s.bind(('hash','sha256'));s.close()",
    "can_raw": "s=socket.socket(socket.AF_CAN,socket.SOCK_RAW,socket.CAN_RAW);s.close()",
    "tipc": "s=socket.socket(socket.AF_TIPC,socket.SOCK_RDM);s.close()",
    "rds": "s=socket.socket(21,socket.SOCK_SEQPACKET,0);s.close()",
    "qrtr": "s=socket.socket(42,socket.SOCK_DGRAM,0);s.close()",
    "llc2": "s=socket.socket(26,socket.SOCK_DGRAM,0);s.close()",
}


def run(*args, check=True, input=None):
    result = subprocess.run(
        [str(arg) for arg in args], input=input, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600,
    )
    print("$", " ".join(str(arg) for arg in args), "\n", result.stdout, flush=True)
    if check and result.returncode:
        raise RuntimeError(f"Command exited {result.returncode}: {args}")
    return result


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2) + "\n")


def loaded():
    return {line.split()[0] for line in Path("/proc/modules").read_text().splitlines()}


def members(path):
    return {
        line.split()[1] for line in path.read_text().splitlines()
        if line.startswith("install ")
    }


def kernel():
    return os.uname().release


def boot_id():
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def download(url, destination):
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    destination.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def check_identity(identity):
    for field, variable in (
        ("name", "MODULEJAIL_POC_VM"),
        ("resourceGroupName", "MODULEJAIL_POC_GROUP"),
        ("subscriptionId", "MODULEJAIL_POC_SUBSCRIPTION"),
    ):
        expected = os.environ.get(variable)
        if not expected:
            raise RuntimeError(f"Controller input required: {variable}")
        if str(identity.get(field, "")).lower() != expected.lower():
            raise RuntimeError(f"Guest identity does not match controller input: {field}")
    return identity


def verify_identity():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(
        "http://169.254.169.254/metadata/instance/compute?api-version=2021-02-01",
        headers={"Metadata": "true"},
    )
    with opener.open(request, timeout=10) as response:
        return check_identity(json.load(response))


def activate(source):
    temporary = POLICY.with_suffix(".tmp")
    shutil.copyfile(source, temporary)
    temporary.chmod(0o644)
    temporary.replace(POLICY)


def probe(state, expected):
    result = run("runuser", "-u", "azureuser", "--", "python3", "-c",
                 "import socket;" + PROBES[state["probe"]], check=False)
    present = state["probe"] in loaded()
    if present != expected or (expected and result.returncode != 0):
        raise RuntimeError(f"Unexpected probe result: loaded={present}, expected={expected}")
    if not expected and result.returncode == 0:
        raise RuntimeError("Blocked socket operation unexpectedly succeeded.")


def unload_probe(state):
    if state["probe"] in loaded():
        run("modprobe", "-r", state["probe"])
    if state["probe"] in loaded():
        raise RuntimeError("Test module remains loaded.")


def journal_event(kind, module, since):
    run("journalctl", "--sync")
    text = run("journalctl", "-t", "modulejail", "--since", since,
               "--no-pager", "-o", "short-iso").stdout
    if f"{kind}: {module}" not in text:
        raise RuntimeError(f"Missing journal event {kind}: {module}")


def workload(state, label):
    run("systemctl", "is-active", "sshd", state["agent_service"])
    run("sshd", "-t")
    run("systemctl", "restart", "sshd")
    run("systemctl", "is-active", "sshd")
    addresses = socket.getaddrinfo("packages.microsoft.com", 443)
    with urllib.request.urlopen("https://packages.microsoft.com/", timeout=30) as response:
        if response.status != 200:
            raise RuntimeError("HTTPS connectivity failed.")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(
        "http://169.254.169.254/metadata/instance?api-version=2021-02-01",
        headers={"Metadata": "true"},
    )
    with opener.open(request, timeout=10) as response:
        metadata = json.load(response)
    check_identity(metadata["compute"])
    sample = ROOT / "storage-test.bin"
    payload = bytes(range(256)) * 16384
    with sample.open("wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    if hashlib.sha256(sample.read_bytes()).digest() != hashlib.sha256(payload).digest():
        raise RuntimeError("Filesystem write/read integrity failed.")
    sample.unlink()
    # A private, accept-only table never replaces the host firewall ruleset.
    run("nft", "add", "table", "inet", "modulejail_poc")
    try:
        run("nft", "-f", "-", input=(
            "add chain inet modulejail_poc output { type filter hook output priority 10; policy accept; }\n"
            "add rule inet modulejail_poc output ct state established,related counter\n"
            "add rule inet modulejail_poc output ip daddr 192.0.2.1 limit rate 10/second counter\n"
        ))
        run("nft", "list", "table", "inet", "modulejail_poc")
    finally:
        run("nft", "delete", "table", "inet", "modulejail_poc")
    save(f"{label}-workload.json", {
        "kernel": kernel(), "boot_id": boot_id(), "dns_results": len(addresses),
        "https": "PASS", "imds": "PASS", "filesystem_io": "PASS",
        "nft_rule_lifecycle": "PASS", "agent_service": state["agent_service"],
        "external_ssh": "requires separate controller-side check",
    })


def prepare(state):
    if state.get("prepared"):
        raise RuntimeError("Prepare already completed; refusing to replace the frozen candidate.")
    os_release = Path("/etc/os-release").read_text()
    if not re.search(r'^VERSION_ID="?4\.0"?$', os_release, re.M):
        raise RuntimeError("Expected Azure Linux 4.0.")
    if POLICY.exists() or HOOK.exists():
        raise RuntimeError("Refusing to overwrite pre-existing ModuleJail configuration.")
    save("guest-identity.json", verify_identity())
    (ROOT / "os-release").write_text(os_release)
    (ROOT / "initial-modules.txt").write_text(Path("/proc/modules").read_text())
    run("tdnf", "-y", "install", "gnupg2", "kmod", "util-linux", "nftables",
        "dracut", "findutils", "gawk", "coreutils")
    for service in ("walinuxagent", "waagent"):
        if run("systemctl", "is-active", service, check=False).returncode == 0:
            state["agent_service"] = service
            break
    else:
        raise RuntimeError("No active Azure Linux agent service.")
    state.update(initial_kernel=kernel(), initial_boot_id=boot_id())
    source = ROOT / "source"
    source.mkdir(exist_ok=True)
    hashes = {}
    for name, url in {
        "v1.6.3.tar.gz": "https://github.com/jnuyens/modulejail/archive/refs/tags/v1.6.3.tar.gz",
        "v1.6.3.tar.gz.sig": "https://github.com/jnuyens/modulejail/releases/download/v1.6.3/v1.6.3.tar.gz.sig",
        "jnuyens.gpg": "https://github.com/jnuyens.gpg",
    }.items():
        hashes[name] = download(url, source / name)
    key_home = ROOT / "gnupg"
    key_home.mkdir(mode=0o700, exist_ok=True)
    run("gpg", "--homedir", key_home, "--batch", "--import", source / "jnuyens.gpg")
    verification = run(
        "gpg", "--homedir", key_home, "--batch", "--status-fd=1",
        "--verify", source / "v1.6.3.tar.gz.sig", source / "v1.6.3.tar.gz",
    ).stdout
    (ROOT / "release-verification.txt").write_text(verification)
    signatures = [line.split() for line in verification.splitlines()
                  if line.startswith("[GNUPG:] VALIDSIG ")]
    if not any(FINGERPRINT in (fields[2], fields[-1]) for fields in signatures):
        raise RuntimeError("Release signature does not match the pinned upstream key.")
    with tarfile.open(source / "v1.6.3.tar.gz") as archive:
        for name in ("modulejail", "LICENSE"):
            member = archive.getmember(f"modulejail-1.6.3/{name}")
            if not member.isfile():
                raise RuntimeError("Unexpected upstream archive member type.")
            (source / name).write_bytes(archive.extractfile(member).read())
    hashes["modulejail"] = hashlib.sha256(TOOL.read_bytes()).hexdigest()
    save("provenance.json", {"version": "1.6.3", "tag_commit": COMMIT,
                             "signer": FINGERPRINT, "sha256": hashes})
    os.environ["MODULEJAIL_NO_UPDATE_CHECK"] = "1"
    run("sh", TOOL, "--version")
    workload(state, "baseline")
    (ROOT / "rpm-inventory.txt").write_text(run("rpm", "-qa").stdout)
    (ROOT / "nft-baseline.txt").write_text(run("nft", "list", "ruleset").stdout)
    shutil.copyfile(f"/boot/config-{kernel()}", ROOT / "kernel-config.txt")
    (ROOT / "boot-files.txt").write_text(run("ls", "-l", "/boot").stdout)
    probe_module = None
    attempts = []
    for module in PROBES:
        info = run("modinfo", "-F", "filename", module, check=False)
        if info.returncode == 0 and ".ko" in info.stdout and module not in loaded():
            result = run("runuser", "-u", "azureuser", "--", "python3", "-c",
                         "import socket;" + PROBES[module], check=False)
            present = module in loaded()
            attempts.append({"module": module, "returncode": result.returncode,
                             "loaded": present, "output": result.stdout})
            if present:
                unload_probe({"probe": module})
            if present and result.returncode == 0:
                probe_module = module
                break
    save("baseline-probe-attempts.json", attempts)
    if probe_module is None:
        raise RuntimeError("No unloaded modular harmless socket probe available.")
    state["probe"] = probe_module
    whitelist = ROOT / "whitelist.conf"
    whitelist.write_text(
        "# Azure guest infrastructure; intermittent Hyper-V dependencies are explicit.\n"
        "hv_vmbus\nhv_storvsc\nhv_netvsc\nhv_utils\nhv_balloon\n"
        "hid_hyperv\npci_hyperv\npci_hyperv_intf\n"
    )
    whitelist.chmod(0o644)
    snapshot = ROOT / "policy-snapshot.txt"
    snapshot.write_text(Path("/proc/modules").read_text())
    # Upstream's fixture interface freezes membership across audit/control policies.
    os.environ["MODULEJAIL_PROC_MODULES"] = str(snapshot)
    common = ["sh", TOOL, "-p", "conservative", "--whitelist-file", whitelist]
    run(*common, "--dry-run", "--verbose", "--output-format", "json")
    run(*common, "--warn-only", "--output-format", "json", "-o", ROOT / "audit.conf")
    run(*common, "--fail-on-module-load", "--output-format", "json", "-o", ROOT / "enforce.conf")
    if members(ROOT / "audit.conf") != members(ROOT / "enforce.conf"):
        raise RuntimeError("Audit and enforcing memberships differ.")
    if probe_module not in members(ROOT / "enforce.conf"):
        raise RuntimeError("Selected probe is not blocked by the conservative policy.")
    whitelist_control = ROOT / "whitelist-control.conf"
    whitelist_control.write_text(whitelist.read_text() + probe_module + "\n")
    run("sh", TOOL, "-p", "conservative", "--whitelist-file", whitelist_control,
        "--fail-on-module-load", "-o", ROOT / "whitelisted.conf")
    if probe_module in members(ROOT / "whitelisted.conf"):
        raise RuntimeError("Explicit whitelist failed to preserve test module.")
    del os.environ["MODULEJAIL_PROC_MODULES"]
    probe(state, True)
    unload_probe(state)
    run("sh", TOOL, "--install-initramfs-hook", "--initramfs-builder", "dracut")
    state["candidate_modules"] = len(members(ROOT / "enforce.conf"))
    state["prepared"] = True
    state.pop("last_error", None)


def audit(state):
    require(state, "prepared")
    since = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    activate(ROOT / "audit.conf")
    unload_probe(state)
    probe(state, True)
    journal_event("would-block", state["probe"], since)
    unload_probe(state)
    workload(state, "audit")
    state["audited"] = True


def enforce(state):
    require(state, "audited")
    state["rollback_verified"] = False
    state["boot_verified"] = False
    state["upgrade_boot_verified"] = False
    state["guest_verdict"] = "INCOMPLETE"
    state["verdict"] = "INCOMPLETE: enforcement validation in progress"
    since = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    activate(ROOT / "enforce.conf")
    unload_probe(state)
    probe(state, False)
    direct = run("modprobe", state["probe"], check=False)
    if direct.returncode == 0 or state["probe"] in loaded():
        raise RuntimeError("Explicit modprobe did not fail closed.")
    journal_event("blocked", state["probe"], since)
    try:
        activate(ROOT / "whitelisted.conf")
        probe(state, True)
        unload_probe(state)
    finally:
        activate(ROOT / "enforce.conf")
    workload(state, "enforce")
    run("dracut", "--force", "--kver", kernel())
    check_initramfs(kernel())
    state["enforced_boot_id"] = boot_id()
    state["enforced"] = True


def require(state, key):
    if not state.get(key):
        raise RuntimeError(f"Prerequisite not complete: {key}")


def check_initramfs(version):
    image = Path(f"/boot/initramfs-{version}.img")
    if not image.is_file():
        raise RuntimeError("Expected dracut initramfs image missing.")
    listing = run("lsinitrd", image).stdout
    (ROOT / f"initramfs-{version}.txt").write_text(listing)
    if "modulejail-blacklist.conf" in listing:
        raise RuntimeError("ModuleJail policy leaked into initramfs.")
    state_hash = hashlib.sha256(image.read_bytes()).hexdigest()
    save(f"initramfs-{version}.json", {"image": str(image), "sha256": state_hash})


def boot(state):
    require(state, "enforced")
    if boot_id() == state["enforced_boot_id"]:
        raise RuntimeError("A controller-initiated reboot is required before this phase.")
    expected = state.get("upgrade_target", state["initial_kernel"])
    if kernel() != expected:
        raise RuntimeError(f"Unexpected boot kernel: {kernel()}, expected {expected}")
    if POLICY.read_bytes() != (ROOT / "enforce.conf").read_bytes():
        raise RuntimeError("Frozen enforcement policy changed across reboot.")
    probe(state, False)
    workload(state, "boot-" + kernel())
    check_initramfs(kernel())
    state["boot_verified"] = True
    state["upgrade_boot_verified"] = bool(state.get("upgrade_target"))
    if state["upgrade_boot_verified"]:
        state["upgrade_status"] = "PASS: booted " + kernel() + " under frozen policy"


def upgrade(state):
    require(state, "boot_verified")
    if state.get("upgrade_attempted"):
        raise RuntimeError("Upgrade phase is one-shot.")
    before = run("rpm", "-q", "--qf", "%{VERSION}-%{RELEASE}.%{ARCH}\n", "kernel").stdout.splitlines()
    run("tdnf", "-y", "upgrade", "--refresh", "kernel")
    after = run("rpm", "-q", "--qf", "%{VERSION}-%{RELEASE}.%{ARCH}\n", "kernel").stdout.splitlines()
    new = set(after) - set(before)
    state["upgrade_attempted"] = True
    if not new:
        state["upgrade_status"] = "INCOMPLETE: no distinct kernel update available"
        return
    if len(new) != 1:
        raise RuntimeError("Expected exactly one new kernel package.")
    target = new.pop()
    if not Path(f"/boot/vmlinuz-{state['initial_kernel']}").exists():
        raise RuntimeError("Original fallback kernel image was not retained.")
    check_initramfs(target)
    state["upgrade_target"] = target
    state["enforced_boot_id"] = boot_id()
    # Boot selection must be inspected on the actual AZL4 image, not assumed.
    state["upgrade_status"] = "PENDING: confirm boot entry selects " + target


def rollback(state):
    require(state, "boot_verified")
    if POLICY.read_bytes() != (ROOT / "enforce.conf").read_bytes():
        raise RuntimeError("Refusing to remove policy modified outside this POC.")
    POLICY.unlink()
    probe(state, True)
    unload_probe(state)
    workload(state, "rollback")
    state["rollback_verified"] = True


def refresh(state):
    require(state, "upgrade_boot_verified")
    run("sh", TOOL, "-p", "conservative", "--whitelist-file", ROOT / "whitelist.conf",
        "--fail-on-module-load", "--output-format", "json", "-o", ROOT / "refreshed.conf")
    frozen = members(ROOT / "enforce.conf")
    refreshed = members(ROOT / "refreshed.conf")
    save("upgrade-policy-diff.json", {
        "kernel": kernel(), "applied": False,
        "newly_blocked_on_regeneration": sorted(refreshed - frozen),
        "no_longer_blocked_on_regeneration": sorted(frozen - refreshed),
        "note": "New policy generated outside modprobe.d; loaded state is post-workload, not the original snapshot.",
    })
    state["upgrade_policy_compared"] = True
    state["upgrade_status"] = "PASS: booted " + kernel() + " under frozen policy"


def main():
    if os.geteuid() != 0:
        raise RuntimeError("Run as root only inside the dedicated disposable guest.")
    phase = sys.argv[1]
    actions = {
        "prepare": prepare, "audit": audit, "enforce": enforce,
        "boot": boot, "upgrade": upgrade, "rollback": rollback,
        "refresh": refresh,
    }
    if phase not in actions:
        raise ValueError(f"Unknown phase {phase}")
    verify_identity()
    ROOT.mkdir(mode=0o755, parents=True, exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    os.environ["MODULEJAIL_NO_UPDATE_CHECK"] = "1"
    with (ROOT / f"{phase}-{time.time_ns()}.log").open("w", buffering=1) as log:
        original_stdout = sys.stdout
        sys.stdout = log
        try:
            actions[phase](state)
            state.pop("last_error", None)
            if state.get("rollback_verified"):
                state["guest_verdict"] = "PASS" if state.get("upgrade_boot_verified") else "INCOMPLETE"
                state["verdict"] = "INCOMPLETE: external SSH requires controller-side qualification"
            save("state.json", state)
            print(f"POC_PHASE_PASS={phase}")
        except Exception as error:
            state["last_error"] = f"{phase}: {type(error).__name__}: {error}"
            save("state.json", state)
            print(state["last_error"])
            raise
        finally:
            sys.stdout = original_stdout
    print(json.dumps(state, indent=2))
    print(f"POC_PHASE_PASS={phase}", flush=True)


if __name__ == "__main__":
    main()
