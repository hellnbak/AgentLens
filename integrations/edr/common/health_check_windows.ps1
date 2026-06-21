$svc = Get-Service -Name "agentlens-endpoint-agent" -ErrorAction SilentlyContinue
$watchdog = Get-Service -Name "agentlens-endpoint-watchdog" -ErrorAction SilentlyContinue
Write-Output "AgentLens Windows health check"
if ($svc) { $svc | Select-Object Name, Status, StartType } else { Write-Output "collector_service=missing" }
if ($watchdog) { $watchdog | Select-Object Name, Status, StartType } else { Write-Output "watchdog_service=missing" }
Get-Process | Where-Object {$_.ProcessName -match "otelcol|agentlens"} | Select-Object ProcessName, Id
Get-NetTCPConnection -LocalPort 4317,4318 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State, OwningProcess
if (Test-Path "C:\ProgramData\agentlens\agent.yaml") { Get-FileHash "C:\ProgramData\agentlens\agent.yaml" -Algorithm SHA256 }
