# Falcon Fusion playbook ideas

1. Trigger: AgentLens central finding `endpoint_missing_heartbeat`.
2. Lookup: CrowdStrike host by hostname, serial, or external ID.
3. Action: RTR health-check script.
4. Branch:
   - collector stopped -> RTR restart service
   - config missing -> RTR reinstall package
   - repeated tamper -> create incident and optionally network contain host
5. Notify: Slack/Jira/SIEM.

Custom IOA ideas:

- `launchctl unload /Library/LaunchDaemons/com.agentlens.endpoint-agent.plist`
- `systemctl disable agentlens-endpoint-agent`
- deletion/modification of `/etc/agentlens/agent.yaml`
- kill signals targeting `otelcol-contrib` or `agentlens-endpoint-watchdog`
