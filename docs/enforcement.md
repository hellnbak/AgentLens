# AgentLens enforcement

AgentLens supports optional Level 1 and Level 2 enforcement while keeping monitor-only operation as the default.

## Levels

### Level 1: response actions

Level 1 reacts to detector findings after they are created. It does not block developers directly. Actions include:

- append audit actions to `data/enforcement/actions.jsonl`
- send a generic webhook
- send a Slack-compatible webhook
- create a Jira issue

The `action-router` service tails `data/findings/findings.jsonl`, evaluates `configs/policies/enforcement.yaml`, and records or sends actions.

Dry-run is enabled by default:

```bash
AGENTLENS_ENFORCEMENT_DRY_RUN=true
```

Set it to `false` only after you have tested policy behavior.

Useful endpoints:

```text
http://localhost:8091/health
http://localhost:8091/actions
http://localhost:8091/metrics
```

## Level 2: CI / PR gates

Level 2 fails CI or PR checks when AgentLens findings violate a gate policy. This is the safest first blocking control because it blocks risky changes before merge rather than trying to fight the developer workstation.

The local gate script is:

```bash
scripts/agentlens-policy-check.py
```

Example:

```bash
python3 scripts/agentlens-policy-check.py \
  --policy configs/policies/enforcement.yaml \
  --findings-file data/findings/findings.jsonl \
  --gate pull_request
```

The script exits:

- `0` when the gate passes
- `1` when findings violate the gate
- `2` when dependencies or configuration are invalid

## Policy file

Policies live in:

```text
configs/policies/enforcement.yaml
```

The default policy is conservative:

- audit all high-risk findings locally
- keep webhooks, Slack, and Jira disabled until configured
- block PR gates for high-risk secrets, DLP, shell-risk, git-risk, IaC-risk, and MCP-risk findings

Allow lists can be added by `rule_id` or `finding_id`.

## Recommended rollout

1. Run with `AGENTLENS_ENFORCEMENT_DRY_RUN=true`.
2. Review `/actions` and `data/enforcement/actions.jsonl`.
3. Enable Slack/generic webhook.
4. Enable Jira only for critical findings.
5. Add the PR gate in warn-only mode.
6. Turn PR gate blocking on for secrets and DLP first.
7. Expand blocking to shell/git/IaC/MCP after tuning false positives.

## Important limitations

Level 1 and Level 2 do not prevent a user from using a local AI tool. They provide response actions and merge-time enforcement. Endpoint and gateway enforcement should be added separately when you want runtime blocking.
