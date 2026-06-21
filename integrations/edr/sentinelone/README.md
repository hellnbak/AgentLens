# SentinelOne integration

Use SentinelOne Remote Script Orchestration for install/repair, Deep Visibility for queries, and STAR rules for automated response.

Suggested automations:

- collector process killed -> restart service
- config modified -> repair package
- missing heartbeat -> run health script
- repeated tamper -> alert or isolate depending on policy
