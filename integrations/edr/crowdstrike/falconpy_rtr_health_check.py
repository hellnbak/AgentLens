#!/usr/bin/env python3
"""CrowdStrike RTR health-check scaffold.

This file is intentionally conservative. It prints the intended RTR command by default.
Wire it to FalconPy Real Time Response Admin APIs in your environment and use --execute only after testing.
"""
import argparse
import os

MAC_CMD = "bash /tmp/agentlens/health_check_macos.sh"
LINUX_CMD = "bash /tmp/agentlens/health_check_linux.sh"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host-id", required=True)
    p.add_argument("--platform", choices=["macos", "linux", "windows"], default="macos")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    cmd = MAC_CMD if args.platform == "macos" else LINUX_CMD if args.platform == "linux" else "powershell -ExecutionPolicy Bypass -File C:\\ProgramData\\agentlens\\health_check_windows.ps1"
    print({"vendor": "crowdstrike", "host_id": args.host_id, "command": cmd, "execute": args.execute})
    if not args.execute:
        print("dry-run only; integrate FalconPy RTR batch session + run command here")
        return
    if not os.getenv("FALCON_CLIENT_ID"):
        raise SystemExit("missing Falcon credentials")
    print("TODO: call FalconPy RTR APIs for put-file/run-command")

if __name__ == "__main__":
    main()
