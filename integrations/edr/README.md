# EDR integrations

EDR integrations are optional. AgentLens does not require an EDR, but EDR platforms are ideal for deployment, health validation, repair, and tamper-evident response.

Supported scaffolding:

- CrowdStrike Falcon Real Time Response
- SentinelOne Remote Script Orchestration / Deep Visibility / STAR guidance
- Microsoft Defender for Endpoint Live Response / Advanced Hunting
- Jamf Protect / Jamf Pro macOS fleet checks
- Tanium, Elastic Defend, Carbon Black, Sophos/Trellix placeholders

EDR should not replace the endpoint OTel collector. The collector gathers Claude Code and AI-agent telemetry; EDR validates that the collector is installed, running, and not tampered with.
