# Detections

Rules live under `configs/rules/` and are expressed as YAML.

Example:

```yaml
rules:
  - id: shell.read_env
    category: shell
    severity: high
    risk_score: 80
    description: Shell command appears to read environment or secret files.
    patterns:
      - '\b(cat|less|more|tail|head|grep|rg)\b.*(\.env|credentials|secrets|id_rsa|id_ed25519|\.aws|\.ssh)'
```

Each rule supports:

| Field | Description |
|---|---|
| `id` | Stable rule ID. |
| `category` | Rule family such as `secret`, `dlp`, `shell`, `git`, `iac`, `mcp`, or `prompt`. |
| `severity` | `low`, `medium`, `high`, or `critical`. |
| `risk_score` | 0-100 numeric risk score. |
| `description` | Human-readable explanation. |
| `patterns` | Regular expressions applied to exported telemetry records. |

Findings are written to `data/findings/findings.jsonl` and exposed at `/findings`.
