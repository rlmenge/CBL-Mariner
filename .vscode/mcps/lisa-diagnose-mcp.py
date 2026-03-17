#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from _mcp_utils import (
    FastMCP,
    StatusDict,
    load_env,
    write_output,
)

mcp = FastMCP("lisa-diagnose")

# Load .env config — may set KOJI_BASE_URL and KOJI_INSECURE_URLS
load_env()

_base_url: str | None = None
_ssl_errors_seen: set[str] = set()
_output_dir = Path(os.environ.get("AZLDEV_WORK_DIR", "base/build/work"), "scratch", "lisa-diagnose")


_ssh_key_path = None
_ip_address_vm = None

# Auto-set base URL from env
if os.environ.get("SSH_KEY_PATH"):
    _ssh_key_path = Path(os.environ["SSH_KEY_PATH"])
if os.environ.get("VM_IP_ADDRESS"):
    _ip_address_vm = os.environ["VM_IP_ADDRESS"]

# Log startup config
if _ssh_key_path and _ip_address_vm:
    print(f"[lisa-diagnose-mcp] SSH Key Path: {_ssh_key_path}", file=sys.stderr)
    print(f"[lisa-diagnose-mcp] VM IP Address: {_ip_address_vm}", file=sys.stderr)

@mcp.tool()
def lisa_vm_cmd(cmd: list[str] | None = None, timeout: int = 5) -> StatusDict:
    """Run a command on the test VM via SSH and return the output. Use this to investigate LISA test failures by fetching logs, configs, or other relevant files from the VM.
    """
    if cmd is None or len(cmd) == 0:
        return {"error": "No command provided. Please specify a command to run on the VM."}
    # check if the ssh key and vm are configured
    if not _ssh_key_path or not _ip_address_vm:
        return {
                "error": (
                    "SSH key path and/or VM IP address not configured. "
                    "Please set the SSH_KEY_PATH and VM_IP_ADDRESS environment variables to enable this tool."
                )
            }

    try:
        req = subprocess.run(
            ["ssh", "-i", str(_ssh_key_path), f"azureuser@{_ip_address_vm}"] + cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}

    output = write_output(req.stdout, output_dir=_output_dir, prefix="lisa_diagnose_")
    return {"output": output, "returncode": req.returncode}


if __name__ == "__main__":
    mcp.run()
