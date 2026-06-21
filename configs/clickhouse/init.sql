CREATE DATABASE IF NOT EXISTS agentlens;
CREATE TABLE IF NOT EXISTS agentlens.otel_logs
(
    ts DateTime64(9) DEFAULT now64(),
    body String,
    raw String
)
ENGINE = MergeTree
ORDER BY ts;
CREATE TABLE IF NOT EXISTS agentlens.findings
(
    ts DateTime DEFAULT now(),
    finding_id String,
    rule_id String,
    category String,
    severity String,
    risk_score UInt16,
    context String,
    raw String
)
ENGINE = MergeTree
ORDER BY (ts, severity, category);
