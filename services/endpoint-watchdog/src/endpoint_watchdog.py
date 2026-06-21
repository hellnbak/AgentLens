#!/usr/bin/env python3
"""
agentlens endpoint watchdog.

Tamper-evident watchdog for developer endpoints running the local OTel Collector.
It checks process state, local OTLP ports, config checksum, launchd/systemd service state,
and emits JSONL events that the local Collector can forward upstream via filelog receiver.

This is tamper-resistant, not tamper-proof. A local administrator can always disable local
software. The objective is to make disablement hard, visible, and centrally alertable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_CONFIG = Path("/etc/agentlens/agent.yaml")
DEFAULT_HASH = Path("/etc/agentlens/agent.yaml.sha256")
DEFAULT_LOG = Path("/var/log/agentlens/endpoint-watchdog.jsonl")
DEFAULT_INTERVAL = 60


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_expected_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(errors="ignore").strip()
    if not text:
        return None
    return text.split()[0]


def tcp_connect(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def run(cmd: List[str], timeout: int = 5) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 99, "", str(e)


def proc_running(names: List[str]) -> bool:
    rc, out, _ = run(["/bin/ps", "axo", "comm,args"], timeout=5)
    if rc != 0:
        return False
    haystack = out.lower()
    return any(n.lower() in haystack for n in names)


def service_state(service_name: str) -> Dict[str, Any]:
    system = platform.system().lower()
    if system == "darwin":
        rc, out, err = run(["/bin/launchctl", "print", f"system/{service_name}"], timeout=5)
        return {"manager": "launchd", "service": service_name, "ok": rc == 0, "detail": out[:500] if out else err[:500]}
    rc, out, err = run(["/bin/systemctl", "is-active", service_name], timeout=5)
    enabled_rc, enabled_out, _ = run(["/bin/systemctl", "is-enabled", service_name], timeout=5)
    return {
        "manager": "systemd",
        "service": service_name,
        "ok": rc == 0 and out == "active",
        "enabled": enabled_rc == 0 and enabled_out == "enabled",
        "detail": out or err,
    }


def restart_service(service_name: str) -> Dict[str, Any]:
    system = platform.system().lower()
    if system == "darwin":
        # Kickstart is safer than unload/load and works with a loaded launch daemon.
        rc, out, err = run(["/bin/launchctl", "kickstart", "-k", f"system/{service_name}"], timeout=10)
        return {"action": "launchctl kickstart", "ok": rc == 0, "detail": out or err}
    rc, out, err = run(["/bin/systemctl", "restart", service_name], timeout=15)
    return {"action": "systemctl restart", "ok": rc == 0, "detail": out or err}


def load_env_file(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def write_event(path: Path, event: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def build_event(args: argparse.Namespace) -> Dict[str, Any]:
    expected = read_expected_hash(Path(args.expected_hash))
    actual = sha256_file(Path(args.config))
    checksum_ok = bool(expected and actual and expected == actual)

    env = load_env_file(Path(args.env_file))
    endpoint_id = os.environ.get("AGENTLENS_ENDPOINT_ID") or env.get("AGENTLENS_ENDPOINT_ID") or socket.gethostname()

    ports = {
        "otlp_grpc_4317": tcp_connect("127.0.0.1", 4317),
        "otlp_http_4318": tcp_connect("127.0.0.1", 4318),
        "collector_metrics_8888": tcp_connect("127.0.0.1", 8888),
    }
    service = service_state(args.collector_service)
    watchdog_service = service_state(args.watchdog_service)
    running = proc_running(["otelcol", "otelcol-contrib"])

    findings: List[str] = []
    if not running:
        findings.append("collector_process_not_found")
    if not ports["otlp_grpc_4317"]:
        findings.append("collector_otlp_grpc_not_listening")
    if not service.get("ok"):
        findings.append("collector_service_inactive")
    if not watchdog_service.get("ok"):
        findings.append("watchdog_service_inactive")
    if expected and actual and expected != actual:
        findings.append("collector_config_checksum_mismatch")
    if expected and actual is None:
        findings.append("collector_config_missing")
    if expected is None:
        findings.append("expected_checksum_missing")

    severity = "info"
    if findings:
        severity = "high" if any("checksum" in f or "missing" in f for f in findings) else "medium"

    return {
        "timestamp": now(),
        "event_type": "agentlens.endpoint_heartbeat",
        "endpoint_id": endpoint_id,
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "severity": severity,
        "collector_running": running,
        "ports": ports,
        "collector_service": service,
        "watchdog_service": watchdog_service,
        "config": {
            "path": str(args.config),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "checksum_ok": checksum_ok,
        },
        "findings": findings,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(DEFAULT_CONFIG))
    p.add_argument("--expected-hash", default=str(DEFAULT_HASH))
    p.add_argument("--env-file", default="/etc/agentlens/agent.env")
    p.add_argument("--log-file", default=str(DEFAULT_LOG))
    p.add_argument("--interval", type=int, default=DEFAULT_INTERVAL)
    p.add_argument("--collector-service", default="com.agentlens.endpoint-agent" if platform.system().lower() == "darwin" else "agentlens-endpoint-agent.service")
    p.add_argument("--watchdog-service", default="com.agentlens.endpoint-watchdog" if platform.system().lower() == "darwin" else "agentlens-endpoint-watchdog.service")
    p.add_argument("--restart", action="store_true", help="Try to restart the collector when it is stopped or not listening")
    p.add_argument("--once", action="store_true")
    args = p.parse_args()

    while True:
        event = build_event(args)
        if args.restart and event["findings"]:
            restart = restart_service(args.collector_service)
            event["restart_attempt"] = restart
        write_event(Path(args.log_file), event)
        if args.once:
            print(json.dumps(event, indent=2, sort_keys=True))
            return 0 if not event["findings"] else 2
        time.sleep(max(args.interval, 15))


if __name__ == "__main__":
    raise SystemExit(main())
