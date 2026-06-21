import hashlib
import json
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
import yaml
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

LOG_FILE = Path(os.getenv("AGENTLENS_LOG_FILE", "/data/otel/agentlens-logs.jsonl"))
TRACE_FILE = Path(os.getenv("AGENTLENS_TRACE_FILE", "/data/otel/agentlens-traces.jsonl"))
FINDINGS_FILE = Path(os.getenv("AGENTLENS_FINDINGS_FILE", "/data/findings/findings.jsonl"))
RULE_DIR = Path(os.getenv("AGENTLENS_RULE_DIR", "/app/rules"))
PRICING_DIR = Path(os.getenv("AGENTLENS_PRICING_DIR", "/app/pricing"))
IDENTITY_CACHE = Path(os.getenv("AGENTLENS_IDENTITY_CACHE", "/data/identity/identity-cache.json"))
WEBHOOK_URL = os.getenv("AGENTLENS_WEBHOOK_URL", "").strip()
MIN_ALERT_RISK = int(os.getenv("AGENTLENS_MIN_ALERT_RISK", "75"))

app = FastAPI(title="AgentLens Detector", version="0.1.0")

findings_total = Counter(
    "agentlens_findings_total",
    "AgentLens findings by category, severity, and rule",
    ["category", "severity", "rule_id"],
)
estimated_cost_total = Counter(
    "agentlens_estimated_cost_usd_total",
    "Estimated AI model cost in USD observed by detector",
    ["provider", "model"],
)
processed_events_total = Counter(
    "agentlens_processed_events_total",
    "Telemetry records processed by detector",
    ["source"],
)
last_processed_timestamp = Gauge(
    "agentlens_last_processed_timestamp_seconds",
    "Unix timestamp of the last processed telemetry record",
)

state = {
    "started_at": time.time(),
    "processed": 0,
    "findings": [],
    "cost_usd": 0.0,
    "last_error": None,
    "endpoints": {},
}
seen_findings = set()

@dataclass
class Rule:
    id: str
    category: str
    severity: str
    risk_score: int
    description: str
    patterns: List[re.Pattern]


def load_rules() -> List[Rule]:
    rules: List[Rule] = []
    if not RULE_DIR.exists():
        return rules
    for path in sorted(RULE_DIR.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for raw in data.get("rules", []):
            compiled = []
            for pattern in raw.get("patterns", []):
                compiled.append(re.compile(pattern, re.MULTILINE | re.DOTALL))
            rules.append(
                Rule(
                    id=raw["id"],
                    category=raw.get("category", "unknown"),
                    severity=raw.get("severity", "medium"),
                    risk_score=int(raw.get("risk_score", 50)),
                    description=raw.get("description", raw["id"]),
                    patterns=compiled,
                )
            )
    return rules


def load_pricing() -> Dict[str, Any]:
    pricing = {"models": {}, "aliases": {}}
    if not PRICING_DIR.exists():
        return pricing
    for path in sorted(PRICING_DIR.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        provider = data.get("provider", path.stem)
        for model, price in (data.get("models") or {}).items():
            pricing["models"][f"{provider}:{model}".lower()] = {
                "provider": provider,
                "model": model,
                "input": float(price.get("input_per_million_tokens", 0)),
                "output": float(price.get("output_per_million_tokens", 0)),
            }
        for alias, target in (data.get("aliases") or {}).items():
            pricing["aliases"][str(alias).lower()] = f"{provider}:{target}".lower()
    return pricing

RULES = load_rules()
PRICING = load_pricing()


def flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(flatten(v, key))
    elif isinstance(obj, list):
        for idx, v in enumerate(obj[:50]):
            key = f"{prefix}.{idx}" if prefix else str(idx)
            out.update(flatten(v, key))
    else:
        out[prefix] = obj
    return out


def stringify_record(record: Dict[str, Any]) -> str:
    # Preserve searchable context while bounding memory.
    try:
        return json.dumps(record, default=str, ensure_ascii=False)[:250000]
    except Exception:
        return str(record)[:250000]


def get_first(flat: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for key in keys:
        if key in flat and flat[key] not in (None, ""):
            return flat[key]
    # Loose suffix match for collector-exported nested structures.
    for wanted in keys:
        for k, v in flat.items():
            if k.endswith(wanted) and v not in (None, ""):
                return v
    return None



def load_identity_cache() -> Dict[str, Any]:
    try:
        if IDENTITY_CACHE.exists():
            with IDENTITY_CACHE.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        state["last_error"] = f"identity cache error: {e}"
    return {"users": {}, "devices": {}, "teams": {}, "source": "none"}


def enrich_identity(ctx: Dict[str, Any], flat: Dict[str, Any]) -> Dict[str, Any]:
    cache = load_identity_cache()
    users = cache.get("users", {}) or {}
    devices = cache.get("devices", {}) or {}
    email = str(ctx.get("user") or get_first(flat, ["user.email", "enduser.email", "device.owner", "owner.email"]) or "").lower()
    endpoint_id = str(get_first(flat, ["endpoint_id", "endpoint.id", "host.id", "device.serial", "host.name"]) or "")
    if email and email in users:
        u = users[email]
        ctx["identity.source"] = cache.get("source", "cache")
        ctx["identity.email"] = email
        ctx["identity.display_name"] = u.get("display_name")
        ctx["identity.department"] = u.get("department")
        ctx["identity.cost_center"] = u.get("cost_center")
        ctx["identity.status"] = u.get("status", "unknown")
        ctx["team"] = ctx.get("team") or u.get("team")
    if endpoint_id and endpoint_id in devices:
        d = devices[endpoint_id]
        ctx["device.identity_source"] = cache.get("source", "cache")
        ctx["device.owner_email"] = d.get("owner_email")
        ctx["device.managed"] = True
        ctx["team"] = ctx.get("team") or d.get("team")
    elif endpoint_id:
        ctx.setdefault("device.managed", False)
    return ctx

def infer_context(record: Dict[str, Any]) -> Dict[str, Any]:
    flat = flatten(record)
    text = stringify_record(record)
    ctx = {
        "timestamp": get_first(flat, ["timeUnixNano", "observedTimeUnixNano", "timestamp", "Time"]),
        "service": get_first(flat, ["service.name", "resource.attributes.service.name.value.stringValue", "resourceSpans.0.resource.attributes.0.value.stringValue"]),
        "user": get_first(flat, ["user.id", "user.name", "enduser.id", "session.user", "ai.user"]),
        "team": get_first(flat, ["team", "team.name", "ai.team", "CLAUDE_CODE_TEAM_NAME"]),
        "repo": get_first(flat, ["git.repository", "vcs.repository.url", "repo", "repository", "project.name"]),
        "model": get_first(flat, ["gen_ai.request.model", "gen_ai.response.model", "model", "model_name", "claude.model"]),
        "provider": get_first(flat, ["gen_ai.provider.name", "provider", "ai.provider"]),
        "session_id": get_first(flat, ["session.id", "session_id", "claude.session.id"]),
        "trace_id": get_first(flat, ["traceId", "trace_id"]),
        "span_id": get_first(flat, ["spanId", "span_id"]),
    }
    ctx = enrich_identity(ctx, flat)
    if not ctx["provider"]:
        if "claude" in text.lower() or "anthropic" in text.lower():
            ctx["provider"] = "anthropic"
        elif "openai" in text.lower() or "gpt-" in text.lower():
            ctx["provider"] = "openai"
        else:
            ctx["provider"] = "generic"
    return ctx


def as_int(value: Any) -> int:
    try:
        if isinstance(value, dict):
            value = value.get("asInt") or value.get("intValue") or value.get("value")
        return int(float(value))
    except Exception:
        return 0


def estimate_cost(record: Dict[str, Any], ctx: Dict[str, Any]) -> float:
    flat = flatten(record)
    input_tokens = as_int(get_first(flat, [
        "gen_ai.usage.input_tokens", "gen_ai.usage.prompt_tokens", "input_tokens", "prompt_tokens", "tokens.input", "usage.input_tokens"
    ]))
    output_tokens = as_int(get_first(flat, [
        "gen_ai.usage.output_tokens", "gen_ai.usage.completion_tokens", "output_tokens", "completion_tokens", "tokens.output", "usage.output_tokens"
    ]))
    if not input_tokens and not output_tokens:
        return 0.0

    provider = str(ctx.get("provider") or "generic").lower()
    model = str(ctx.get("model") or "unknown").lower()
    key = f"{provider}:{model}"
    if key not in PRICING["models"]:
        for alias, target in PRICING["aliases"].items():
            if alias in model:
                key = target
                break
    price = PRICING["models"].get(key) or PRICING["models"].get("generic:unknown")
    if not price:
        return 0.0
    cost = (input_tokens / 1_000_000 * price["input"]) + (output_tokens / 1_000_000 * price["output"])
    if cost > 0:
        estimated_cost_total.labels(price["provider"], price["model"]).inc(cost)
        state["cost_usd"] += cost
    return cost


def mask_match(value: str) -> str:
    if len(value) <= 12:
        return "[REDACTED]"
    return value[:4] + "...[REDACTED]..." + value[-4:]


def make_finding(rule: Rule, match: str, record: Dict[str, Any], ctx: Dict[str, Any], cost: float) -> Dict[str, Any]:
    body_hash = hashlib.sha256(stringify_record(record).encode("utf-8", errors="ignore")).hexdigest()
    finding_id = hashlib.sha256(f"{rule.id}:{match}:{body_hash}".encode()).hexdigest()[:24]
    return {
        "finding_id": finding_id,
        "ts": time.time(),
        "rule_id": rule.id,
        "category": rule.category,
        "severity": rule.severity,
        "risk_score": rule.risk_score,
        "description": rule.description,
        "match": mask_match(match),
        "context": ctx,
        "estimated_cost_usd": round(cost, 8),
        "record_hash": body_hash,
    }


def write_finding(finding: Dict[str, Any]) -> None:
    FINDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with FINDINGS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(finding, ensure_ascii=False) + "\n")


def send_alert(finding: Dict[str, Any]) -> None:
    if not WEBHOOK_URL or finding["risk_score"] < MIN_ALERT_RISK:
        return
    try:
        requests.post(WEBHOOK_URL, json={"text": f"AgentLens finding: {finding['rule_id']} risk={finding['risk_score']}", "finding": finding}, timeout=3)
    except Exception as e:
        state["last_error"] = f"webhook error: {e}"


def update_endpoint_state(record: Dict[str, Any]) -> None:
    flat = flatten(record)
    text = stringify_record(record)
    if "agentlens.endpoint_heartbeat" not in text and "endpoint_heartbeat" not in text:
        return
    endpoint_id = get_first(flat, ["endpoint_id", "endpoint.id", "attributes.endpoint.id", "body.endpoint_id"]) or "unknown"
    findings = []
    for k, v in flat.items():
        if k.endswith("findings") and isinstance(v, str):
            findings.append(v)
    # Fall back to string search because collector-exported records can be deeply nested.
    known = [
        "collector_process_not_found",
        "collector_otlp_grpc_not_listening",
        "collector_service_inactive",
        "watchdog_service_inactive",
        "collector_config_checksum_mismatch",
        "collector_config_missing",
        "expected_checksum_missing",
    ]
    findings.extend([x for x in known if x in text])
    state["endpoints"][str(endpoint_id)] = {
        "last_seen": time.time(),
        "last_seen_iso": datetime_now(),
        "status": "unhealthy" if findings else "healthy",
        "findings": sorted(set(findings)),
    }


def datetime_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def process_record(record: Dict[str, Any], source: str) -> None:
    state["processed"] += 1
    processed_events_total.labels(source).inc()
    last_processed_timestamp.set(time.time())
    update_endpoint_state(record)
    ctx = infer_context(record)
    cost = estimate_cost(record, ctx)
    text = stringify_record(record)
    for rule in RULES:
        for pattern in rule.patterns:
            for match in pattern.finditer(text):
                snippet = match.group(0)[:1000]
                finding = make_finding(rule, snippet, record, ctx, cost)
                if finding["finding_id"] in seen_findings:
                    continue
                seen_findings.add(finding["finding_id"])
                state["findings"].append(finding)
                state["findings"] = state["findings"][-500:]
                findings_total.labels(rule.category, rule.severity, rule.id).inc()
                write_finding(finding)
                send_alert(finding)


def follow_file(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                process_record(record, source)
            except Exception as e:
                state["last_error"] = f"{source} parse/process error: {e}"


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "rules_loaded": len(RULES),
        "pricing_models_loaded": len(PRICING.get("models", {})),
        "processed": state["processed"],
        "endpoints_seen": len(state.get("endpoints", {})),
        "last_error": state["last_error"],
    }


@app.get("/findings")
def findings(limit: int = 100) -> List[Dict[str, Any]]:
    return list(reversed(state["findings"][-limit:]))


@app.get("/endpoints")
def endpoints(stale_after_seconds: int = 300) -> Dict[str, Any]:
    now_ts = time.time()
    out = {}
    for endpoint_id, info in state["endpoints"].items():
        item = dict(info)
        item["age_seconds"] = round(now_ts - float(info.get("last_seen", 0)), 2)
        if item["age_seconds"] > stale_after_seconds:
            item["status"] = "stale"
        out[endpoint_id] = item
    return {"count": len(out), "endpoints": out}


@app.get("/stats")
def stats() -> Dict[str, Any]:
    by_category: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    for f in state["findings"]:
        by_category[f["category"]] = by_category.get(f["category"], 0) + 1
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1
    return {
        "uptime_seconds": round(time.time() - state["started_at"], 2),
        "processed": state["processed"],
        "recent_findings_count": len(state["findings"]),
        "estimated_cost_usd": round(state["cost_usd"], 8),
        "by_category": by_category,
        "by_severity": by_severity,
        "last_error": state["last_error"],
    }


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


def main() -> None:
    threads = [
        threading.Thread(target=follow_file, args=(LOG_FILE, "logs"), daemon=True),
        threading.Thread(target=follow_file, args=(TRACE_FILE, "traces"), daemon=True),
    ]
    for t in threads:
        t.start()
    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")


if __name__ == "__main__":
    main()
