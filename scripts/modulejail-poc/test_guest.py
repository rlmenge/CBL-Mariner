import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("guest", Path(__file__).with_name("guest.py"))
guest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guest)
SUMMARY_SPEC = importlib.util.spec_from_file_location("summary", Path(__file__).with_name("summarize.py"))
summary = importlib.util.module_from_spec(SUMMARY_SPEC)
SUMMARY_SPEC.loader.exec_module(summary)
SCRATCH = (Path(__file__).resolve().parents[2] / "base" / "build" / "work"
           / "scratch" / "modulejail-poc-tests")


def temporary_directory():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=SCRATCH)


class PocTests(unittest.TestCase):
    def test_activation_replaces_only_the_named_policy(self):
        with temporary_directory() as directory:
            root = Path(directory)
            source = root / "enforce.conf"
            source.write_text("install can_raw /bin/false\n")
            policy = root / "modulejail-blacklist.conf"
            unrelated = root / "other.conf"
            unrelated.write_text("keep me\n")
            with patch.object(guest, "POLICY", policy):
                guest.activate(source)
            self.assertEqual(policy.read_bytes(), source.read_bytes())
            self.assertEqual(unrelated.read_text(), "keep me\n")
            self.assertFalse(policy.with_suffix(".tmp").exists())

    def test_blocked_probe_requires_absence_and_failed_operation(self):
        for returncode, modules in ((0, set()), (1, {"can_raw"})):
            with self.subTest(returncode=returncode, modules=modules):
                result = guest.subprocess.CompletedProcess([], returncode)
                with patch.object(guest, "run", return_value=result), \
                        patch.object(guest, "loaded", return_value=modules):
                    with self.assertRaises(RuntimeError):
                        guest.probe({"probe": "can_raw"}, False)

    def test_probe_runs_as_unprivileged_user(self):
        result = guest.subprocess.CompletedProcess([], 1)
        with patch.object(guest, "run", return_value=result) as command, \
                patch.object(guest, "loaded", return_value=set()):
            guest.probe({"probe": "can_raw"}, False)
        self.assertEqual(command.call_args.args[:6],
                         ("runuser", "-u", "azureuser", "--", "python3", "-c"))

    def test_boot_requires_an_actual_reboot(self):
        state = {"enforced": True, "enforced_boot_id": "unchanged"}
        with patch.object(guest, "boot_id", return_value="unchanged"):
            with self.assertRaisesRegex(RuntimeError, "reboot"):
                guest.boot(state)

    def test_no_kernel_update_is_incomplete_not_a_pass(self):
        package = guest.subprocess.CompletedProcess([], 0, stdout="6.18.50-1.5.azl4.x86_64\n")
        state = {"boot_verified": True}
        with patch.object(guest, "run", return_value=package):
            guest.upgrade(state)
        self.assertIn("INCOMPLETE", state["upgrade_status"])
        self.assertNotIn("upgrade_target", state)
        self.assertNotIn("upgrade_boot_verified", state)

    def test_failed_phase_persists_error_without_success_marker(self):
        with temporary_directory() as directory:
            root = Path(directory)
            output = io.StringIO()
            with patch.object(guest, "ROOT", root), \
                    patch.object(guest, "STATE", root / "state.json"), \
                    patch.object(guest, "verify_identity"), \
                    patch.object(guest.os, "geteuid", return_value=0, create=True), \
                    patch.object(guest.sys, "argv", ["guest.py", "audit"]), \
                    contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(RuntimeError, "prepared"):
                    guest.main()
            state = guest.json.loads((root / "state.json").read_text())
            self.assertIn("audit:", state["last_error"])
            self.assertNotIn("POC_PHASE_PASS", output.getvalue())

    def test_guest_success_does_not_imply_external_ssh_pass(self):
        with temporary_directory() as directory:
            root = Path(directory)
            state_path = root / "state.json"
            state_path.write_text(guest.json.dumps({
                "rollback_verified": True, "upgrade_boot_verified": True,
            }))
            with patch.object(guest, "ROOT", root), \
                    patch.object(guest, "STATE", state_path), \
                    patch.object(guest, "verify_identity"), \
                    patch.object(guest.os, "geteuid", return_value=0, create=True), \
                    patch.object(guest.sys, "argv", ["guest.py", "refresh"]), \
                    patch.object(guest, "refresh"), \
                    contextlib.redirect_stdout(io.StringIO()):
                guest.main()
            state = guest.json.loads(state_path.read_text())
            self.assertEqual(state["guest_verdict"], "PASS")
            self.assertTrue(state["verdict"].startswith("INCOMPLETE"))

    def test_latest_ssh_failure_is_not_hidden_by_earlier_success(self):
        with temporary_directory() as directory:
            root = Path(directory)
            record = {
                "phase": "enforce", "passed": True, "exit_code": 0,
                "output": "POLICY=present kernel-test old-boot EXTERNAL_SSH_PASS",
            }
            (root / "ssh-001.json").write_text(guest.json.dumps(record))
            record.update(passed=False, exit_code=255)
            (root / "ssh-002.json").write_text(guest.json.dumps(record))
            checks = summary.ssh_checks(
                root, {"enforced_boot_id": "old-boot", "upgrade_target": "kernel-test"}, "new-boot",
            )
            self.assertFalse(any(checks.values()))

    def test_summary_rejects_modified_archive_before_extraction(self):
        with temporary_directory() as directory:
            root = Path(directory)
            (root / "evidence.tar.gz").write_bytes(b"modified")
            (root / "evidence.sha256").write_text("0" * 64)
            with self.assertRaisesRegex(RuntimeError, "SHA256"):
                summary.summarize(root)

    def test_identity_requires_explicit_controller_inputs(self):
        with patch.dict(guest.os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Controller input"):
                guest.check_identity({})

    def test_identity_rejects_a_different_resource_group(self):
        inputs = {
            "MODULEJAIL_POC_VM": "modulejail-poc-x64",
            "MODULEJAIL_POC_GROUP": "rlmenge-modulejail-poc-test",
            "MODULEJAIL_POC_SUBSCRIPTION": "11111111-1111-1111-1111-111111111111",
        }
        identity = {
            "name": inputs["MODULEJAIL_POC_VM"],
            "subscriptionId": inputs["MODULEJAIL_POC_SUBSCRIPTION"],
            "resourceGroupName": "another-group",
        }
        with patch.dict(guest.os.environ, inputs):
            with self.assertRaisesRegex(RuntimeError, "resourceGroupName"):
                guest.check_identity(identity)


if __name__ == "__main__":
    unittest.main()
