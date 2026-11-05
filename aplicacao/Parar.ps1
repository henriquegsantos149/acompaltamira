$ErrorActionPreference = 'Stop'
$codexRoot = Split-Path $PSScriptRoot -Parent
$statePath = Join-Path $codexRoot 'verificacao/dashboard/servidor.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Host 'Nenhum servidor iniciado por este atalho foi registrado.'; exit 0 }
$serverInfo = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
$targetProcess = Get-Process -Id $serverInfo.pid -ErrorAction SilentlyContinue
if (-not $targetProcess) { Write-Host 'O servidor já foi encerrado.'; exit 0 }
$actualStart = $targetProcess.StartTime.ToUniversalTime()
$expectedStart = [DateTime]::Parse($serverInfo.started).ToUniversalTime()
$processDetails = Get-CimInstance Win32_Process -Filter "ProcessId = $($serverInfo.pid)"
if ([Math]::Abs(($actualStart-$expectedStart).TotalSeconds) -gt 1 -or $processDetails.CommandLine -notlike '*uvicorn app.main:app*' -or $processDetails.CommandLine -notlike '*8765*') {
    throw 'O processo não corresponde ao servidor registrado. Nenhum processo foi encerrado.'
}
# The local API provides an orderly shutdown endpoint; do not forcibly kill SQLite writers.
try {
    Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/session/write' -Method Post -ContentType 'application/json' -Body '{"confirm_sync_paused":false}' | Out-Null
} catch {
    throw 'Não foi possível encerrar a sessão de escrita. Feche-a na interface antes de parar o serviço.'
}
Stop-Process -Id $serverInfo.pid
Write-Host 'Servidor PMISB encerrado. A sincronização pode ser retomada após concluir os backups.'
