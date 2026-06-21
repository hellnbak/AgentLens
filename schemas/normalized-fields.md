# Normalized fields

AgentLens does not require every AI coding platform to emit the same attributes. Instead, it normalizes common fields where possible.

| Field | Purpose |
|---|---|
| `event_type` | Normalized event family, for example `ai.prompt`, `ai.tool_call`, `ai.security_finding`. |
| `platform` | Source platform, for example `claude_code`. |
| `provider` | Model provider, for example `anthropic`, `openai`, `generic`. |
| `model` | Model name or alias. |
| `user` | User identity when available. |
| `team` | Team/business unit when available. |
| `repo` | Repository/project when available. |
| `session_id` | AI coding session identifier. |
| `trace_id` | OTel trace ID. |
| `span_id` | OTel span ID. |
| `tool_name` | Tool invoked by the AI assistant. |
| `command` | Shell/git command when present and allowed by policy. |
| `input_tokens` | Input/prompt token count. |
| `output_tokens` | Output/completion token count. |
| `estimated_cost_usd` | Best-effort estimated cost based on pricing config. |
| `risk_score` | 0-100 risk score from rules/detectors. |
| `dlp_findings` | DLP/secret finding categories. |
