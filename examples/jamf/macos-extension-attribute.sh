#!/usr/bin/env bash
# Jamf Extension Attribute: AgentLens endpoint status
if launchctl print system/com.agentlens.endpoint-agent >/dev/null 2>&1 && \
   launchctl print system/com.agentlens.endpoint-watchdog >/dev/null 2>&1; then
  echo "<result>Installed</result>"
else
  echo "<result>Missing or Stopped</result>"
fi
