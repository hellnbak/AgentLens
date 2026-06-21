# Deep Visibility query examples

```text
ProcessName Contains Anycase "otelcol" OR ProcessName Contains Anycase "agentlens"
```

```text
FilePath Contains Anycase "/etc/agentlens" OR FilePath Contains Anycase "com.agentlens"
```

```text
TgtProcName Contains Anycase "otelcol" AND EventType = "Process Exit"
```

```text
CmdLine Contains Anycase "systemctl disable agentlens" OR CmdLine Contains Anycase "launchctl unload" AND CmdLine Contains Anycase "agentlens"
```
