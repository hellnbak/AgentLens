# Microsoft Defender / Intune remediation

Detection script:

- verify AgentLens service exists
- verify local OTLP listener on 4317/4318
- verify config checksum
- exit 1 if unhealthy

Remediation script:

- reinstall or restart AgentLens endpoint collector
- restore managed config
- restart watchdog

Pair with Defender Advanced Hunting queries in `advanced-hunting.kql`.
