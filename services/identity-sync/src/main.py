import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests
import yaml

PROVIDER = os.getenv("AGENTLENS_IDP_PROVIDER", "static").lower()
ENABLED = os.getenv("AGENTLENS_IDP_ENABLED", "false").lower() == "true"
STATIC_MAP = Path(os.getenv("AGENTLENS_IDENTITY_MAP", "/app/identity/static-identity-map.yaml"))
OUT = Path(os.getenv("AGENTLENS_IDENTITY_CACHE", "/data/identity/identity-cache.json"))
SYNC_INTERVAL = int(os.getenv("AGENTLENS_IDP_SYNC_INTERVAL_SECONDS", "900"))


def load_static() -> Dict[str, Any]:
    if not STATIC_MAP.exists():
        return {"users": {}, "devices": {}, "teams": {}, "source": "static", "synced_at": time.time()}
    with STATIC_MAP.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("users", {})
    data.setdefault("devices", {})
    data.setdefault("teams", {})
    data["source"] = "static"
    data["synced_at"] = time.time()
    return data


def sync_okta() -> Dict[str, Any]:
    org = os.getenv("OKTA_ORG_URL", "").rstrip("/")
    token = os.getenv("OKTA_API_TOKEN", "")
    if not org or not token:
        raise RuntimeError("OKTA_ORG_URL and OKTA_API_TOKEN are required for Okta sync")
    headers = {"Authorization": f"SSWS {token}", "Accept": "application/json"}
    users: Dict[str, Any] = {}
    url = f"{org}/api/v1/users?limit=200"
    # Minimal scaffold: first page plus Link-following can be extended.
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    for u in resp.json():
        profile = u.get("profile", {})
        email = (profile.get("email") or profile.get("login") or "").lower()
        if not email:
            continue
        users[email] = {
            "display_name": profile.get("displayName") or f"{profile.get('firstName','')} {profile.get('lastName','')}",
            "team": profile.get("department") or profile.get("organization"),
            "department": profile.get("department"),
            "cost_center": profile.get("costCenter"),
            "manager": profile.get("manager"),
            "status": u.get("status"),
            "groups": [],
        }
    return {"users": users, "devices": {}, "teams": {}, "source": "okta", "synced_at": time.time()}


def sync_jumpcloud() -> Dict[str, Any]:
    key = os.getenv("JUMPCLOUD_API_KEY", "")
    org_id = os.getenv("JUMPCLOUD_ORG_ID", "")
    if not key:
        raise RuntimeError("JUMPCLOUD_API_KEY is required for JumpCloud sync")
    headers = {"x-api-key": key, "Accept": "application/json"}
    if org_id:
        headers["x-org-id"] = org_id
    users: Dict[str, Any] = {}
    systems: Dict[str, Any] = {}
    u_resp = requests.get("https://console.jumpcloud.com/api/systemusers?limit=100", headers=headers, timeout=20)
    u_resp.raise_for_status()
    for u in u_resp.json().get("results", []):
        email = (u.get("email") or u.get("username") or "").lower()
        if not email:
            continue
        users[email] = {
            "display_name": f"{u.get('firstname','')} {u.get('lastname','')}",
            "team": u.get("department"),
            "department": u.get("department"),
            "cost_center": None,
            "manager": None,
            "status": "active" if u.get("activated") else "inactive",
            "groups": [],
        }
    s_resp = requests.get("https://console.jumpcloud.com/api/systems?limit=100", headers=headers, timeout=20)
    s_resp.raise_for_status()
    for s in s_resp.json().get("results", []):
        serial = s.get("serialNumber") or s.get("id")
        if serial:
            systems[serial] = {"hostname": s.get("hostname"), "os": s.get("os"), "system_id": s.get("id")}
    return {"users": users, "devices": systems, "teams": {}, "source": "jumpcloud", "synced_at": time.time()}


def sync_once() -> Dict[str, Any]:
    base = load_static()
    if not ENABLED:
        return base
    if PROVIDER == "okta":
        data = sync_okta()
    elif PROVIDER == "jumpcloud":
        data = sync_jumpcloud()
    elif PROVIDER == "static":
        data = base
    else:
        raise RuntimeError(f"unsupported provider: {PROVIDER}")
    # Preserve static teams/budgets as a fallback overlay.
    data.setdefault("teams", {})
    data["teams"].update(base.get("teams", {}))
    return data


def write_cache(data: Dict[str, Any]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(OUT)


def main() -> None:
    while True:
        try:
            data = sync_once()
            write_cache(data)
            print(f"identity sync ok provider={data.get('source')} users={len(data.get('users', {}))}", flush=True)
        except Exception as e:
            print(f"identity sync error: {e}", flush=True)
        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    main()
