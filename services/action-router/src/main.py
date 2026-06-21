import hashlib
import json
import os
import time
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
import yaml
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

FINDINGS_FILE = Path(os.getenv("AGENTLENS_FINDINGS_FILE", "/data/findings/findings.jsonl"))
POLICY_FILE = Path(os.getenv("AGENTLENS_POLICY_FILE", "/app/policies/enforcement.yaml"))
ACTIONS_FILE = Path(os.getenv("AGENTLENS_ACTIONS_FILE", "/data/enforcement/actions.jsonl"))
DRY_RUN = os.getenv("AGENTLENS_ENFORCEMENT_DRY_RUN", "true").lower() in {"1", "true", "yes"}
PORT = int(os.getenv("AGENTLENS_ACTION_ROUTER_PORT", "8091"))

app = FastAPI(title="AgentLens Action Router", version="0.2.0")

actions_total = Counter("agentlens_actions_total", "AgentLens enforcement actions", ["action", "status"])
policy_matches_total = Counter("agentlens_policy_matches_total", "AgentLens policy matches", ["policy_id", "level"])
last_action_timestamp = Gauge("agentlens_last_action_timestamp_seconds", "Last AgentLens action timestamp")

state: Dict[str, Any] = {
    "started_at": time.time(),
    "processed_findings": 0,
    "actions": [],
    "last_error": None,
    "dry_run": DRY_RUN,
}
seen_actions = set()


def load_policy() -> Dict[str, Any]:
    if not POLICY_FILE.exists():
        return {"defaults": {"dry_run": True}, "policies": []}
    with POLICY_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def env_value(name: str) -> str:
    return os.getenv(name, "").strip()


def as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def finding_matches(finding: Dict[str, Any], match: Dict[str, Any]) -> bool:
    if not match:
        return True
    risk = int(finding.get("risk_score") or 0)
    if risk < int(match.get("min_risk_score", 0)):
        return False
    categories = set(as_list(match.get("categories")))
    if categories and str(finding.get("category")) not in categories:
        return False
    severities = set(as_list(match.get("severities")))
    if severities and str(finding.get("severity")) not in severities:
        return False
    rule_ids = set(as_list(match.get("rule_ids")))
    if rule_ids and str(finding.get("rule_id")) not in rule_ids:
        return False
    return True


def action_key(policy_id: str, action: str, finding: Dict[str, Any]) -> str:
    fid = finding.get("finding_id") or finding.get("record_hash") or json.dumps(finding, sort_keys=True)[:500]
    return hashlib.sha256(f"{policy_id}:{action}:{fid}".encode()).hexdigest()


def write_action(event: Dict[str, Any]) -> None:
    ACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ACTIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    state["actions"].append(event)
    state["actions"] = state["actions"][-500:]
    last_action_timestamp.set(time.time())


def build_action_event(policy: Dict[str, Any], action: str, finding: Dict[str, Any], status: str, detail: str = "") -> Dict[str, Any]:
    return {
        "ts": time.time(),
        "policy_id": policy.get("id"),
        "level": policy.get("level"),
        "action": action,
        "status": status,
        "dry_run": DRY_RUN,
        "detail": detail,
        "finding_id": finding.get("finding_id"),
        "rule_id": finding.get("rule_id"),
        "category": finding.get("category"),
        "severity": finding.get("severity"),
        "risk_score": finding.get("risk_score"),
        "context": finding.get("context", {}),
    }


def post_json(url: str, payload: Dict[str, Any], timeout: int = 5) -> str:
    if DRY_RUN:
        return "dry-run"
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return f"http {resp.status_code}"


def run_file_audit(policy: Dict[str, Any], action: str, finding: Dict[str, Any]) -> None:
    event = build_action_event(policy, action, finding, "recorded")
    write_action(event)
    actions_total.labels(action, "recorded").inc()


def run_webhook(policy: Dict[str, Any], action: str, finding: Dict[str, Any], url: str) -> None:
    payload = {
        "source": "agentlens",
        "policy_id": policy.get("id"),
        "action": action,
        "finding": finding,
        "summary": f"AgentLens {finding.get('severity')} {finding.get('category')} finding: {finding.get('rule_id')}",
    }
    detail = post_json(url, payload)
    event = build_action_event(policy, action, finding, "sent", detail)
    write_action(event)
    actions_total.labels(action, "sent").inc()


def run_slack(policy: Dict[str, Any], action: str, finding: Dict[str, Any], url: str) -> None:
    ctx = finding.get("context", {}) or {}
    text = (
        f"AgentLens finding: *{finding.get('severity')}* / *{finding.get('category')}*\n"
        f"Rule: `{finding.get('rule_id')}` Risk: `{finding.get('risk_score')}`\n"
        f"User: `{ctx.get('identity.email') or ctx.get('user') or 'unknown'}` Repo: `{ctx.get('repo') or 'unknown'}`"
    )
    detail = post_json(url, {"text": text, "finding": finding})
    event = build_action_event(policy, action, finding, "sent", detail)
    write_action(event)
    actions_total.labels(action, "sent").inc()


def run_jira(policy: Dict[str, Any], action: str, finding: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    base_url = env_value(cfg.get("base_url_env", "JIRA_BASE_URL")).rstrip("/")
    email = env_value(cfg.get("email_env", "JIRA_EMAIL"))
    token = env_value(cfg.get("api_token_env", "JIRA_API_TOKEN"))
    project_key = env_value(cfg.get("project_key_env", "JIRA_PROJECT_KEY"))
    if not all([base_url, email, token, project_key]):
        event = build_action_event(policy, action, finding, "skipped", "missing Jira environment variables")
        write_action(event)
        actions_total.labels(action, "skipped").inc()
        return
    fields = {
        "project": {"key": project_key},
        "summary": f"AgentLens: {finding.get('severity')} {finding.get('rule_id')}",
        "issuetype": {"name": cfg.get("issue_type", "Task")},
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": json.dumps(finding, indent=2)[:30000]}]},
            ],
        },
    }
    if not DRY_RUN:
        resp = requests.post(
            f"{base_url}/rest/api/3/issue",
            auth=(email, token),
            json={"fields": fields},
            timeout=10,
        )
        resp.raise_for_status()
        detail = f"created {resp.json().get('key')}"
    else:
        detail = "dry-run"
    event = build_action_event(policy, action, finding, "sent", detail)
    write_action(event)
    actions_total.labels(action, "sent").inc()


def execute_actions(policy: Dict[str, Any], finding: Dict[str, Any]) -> None:
    config = load_policy()
    actions_cfg = config.get("level1_actions", {}) or {}
    for action in policy.get("actions", []):
        key = action_key(policy.get("id", "unknown"), action, finding)
        if key in seen_actions:
            continue
        seen_actions.add(key)
        try:
            cfg = actions_cfg.get(action, {}) or {}
            if action != "file_audit" and cfg.get("enabled") is False:
                run_file_audit(policy, f"{action}:disabled", finding)
                continue
            min_risk = int(cfg.get("min_risk_score", 0))
            if int(finding.get("risk_score") or 0) < min_risk:
                continue
            if action == "file_audit":
                run_file_audit(policy, action, finding)
            elif action == "generic_webhook":
                url = env_value(cfg.get("url_env", "AGENTLENS_ACTION_WEBHOOK_URL"))
                if url:
                    run_webhook(policy, action, finding, url)
                else:
                    run_file_audit(policy, "generic_webhook:missing_url", finding)
            elif action == "slack_webhook":
                url = env_value(cfg.get("url_env", "AGENTLENS_SLACK_WEBHOOK_URL"))
                if url:
                    run_slack(policy, action, finding, url)
                else:
                    run_file_audit(policy, "slack_webhook:missing_url", finding)
            elif action == "jira":
                run_jira(policy, action, finding, cfg)
            else:
                run_file_audit(policy, f"unknown:{action}", finding)
        except Exception as exc:
            state["last_error"] = f"action {action} failed: {exc}"
            event = build_action_event(policy, action, finding, "error", str(exc))
            write_action(event)
            actions_total.labels(action, "error").inc()


def process_finding(finding: Dict[str, Any]) -> None:
    state["processed_findings"] += 1
    config = load_policy()
    for policy in config.get("policies", []) or []:
        if not policy.get("enabled", True) or int(policy.get("level", 1)) != 1:
            continue
        if finding_matches(finding, policy.get("match", {}) or {}):
            policy_matches_total.labels(policy.get("id", "unknown"), str(policy.get("level", 1))).inc()
            execute_actions(policy, finding)


def follow_findings() -> None:
    FINDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS_FILE.touch(exist_ok=True)
    with FINDINGS_FILE.open("r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            try:
                process_finding(json.loads(line))
            except Exception as exc:
                state["last_error"] = f"process finding error: {exc}"


@app.get("/health")
def health() -> Dict[str, Any]:
    policy = load_policy()
    return {
        "ok": True,
        "dry_run": DRY_RUN,
        "processed_findings": state["processed_findings"],
        "actions_recorded": len(state["actions"]),
        "policies_loaded": len(policy.get("policies", []) or []),
        "last_error": state["last_error"],
    }


@app.get("/actions")
def actions(limit: int = 100) -> List[Dict[str, Any]]:
    return list(reversed(state["actions"][-limit:]))


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


def main() -> None:
    t = threading.Thread(target=follow_findings, daemon=True)
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")


if __name__ == "__main__":
    main()
