param([switch]$SemAbrir)
$ErrorActionPreference = 'Stop'
$appRoot = $PSScriptRoot
$codexRoot = Split-Path $appRoot -Parent
$backendRoot = Join-Path $appRoot 'backend'
$frontendBuild = Join-Path $appRoot 'frontend/dist/index.html'
$taskLogRoot = Join-Path $codexRoot 'verificacao/dashboard'
New-Item -ItemType Directory -Force -Path $taskLogRoot | Out-Null
$taskUrl = 'http://127.0.0.1:8765'
try {
    $existingHealth = Invoke-RestMethod -Uri "$taskUrl/api/health" -TimeoutSec 2
    if ($existingHealth.status -eq 'ok' -and $existingHealth.version -eq '1.0') {
        Write-Host "PMISB disponível em $taskUrl"
        if (-not $SemAbrir) { Start-Process $taskUrl }
        exit 0
    }
    throw 'A porta8765 está sendo usada por outro serviço.'
} catch {
    if ($_.Exception.Message -like '*outro serviço*') { throw }
}
if (-not (Test-Path -LiteralPath $frontendBuild)) {
    throw 'Interface não compilada. Execute Instalar.ps1 antes de iniciar.'
}
$venvPython = Join-Path $backendRoot '.venv/Scripts/python.exe'
$taskPython = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python -ErrorAction Stop).Source }
& $taskPython -c 'import fastapi,uvicorn'
if ($LASTEXITCODE -ne 0) { throw 'Dependências Python ausentes. Execute Instalar.ps1.' }
$stdoutPath = Join-Path $taskLogRoot 'servidor.stdout.log'
$stderrPath = Join-Path $taskLogRoot 'servidor.stderr.log'
$serverProcess = Start-Process -FilePath $taskPython -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8765') -WorkingDirectory $backendRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru
@{pid=$serverProcess.Id;started=$serverProcess.StartTime.ToUniversalTime().ToString('o');python=$taskPython;port=8765} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskLogRoot 'servidor.json') -Encoding utf8
$ready = $false
for ($attempt=0; $attempt -lt 60; $attempt++) {
    if ($serverProcess.HasExited) { break }
    try {
        $taskHealth = Invoke-RestMethod -Uri "$taskUrl/api/health" -TimeoutSec 1
        if ($taskHealth.status -eq 'ok') { $ready=$true; break }
    } catch { }
    Start-Sleep -Milliseconds 250
}
if (-not $ready) {
    $errorTail = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Tail 12 | Out-String } else { '' }
    throw "O servidor não iniciou. Consulte verificacao/dashboard/servidor.stderr.log. $errorTail"
}
Write-Host "PMISB disponível em $taskUrl — modo consulta."
if (-not $SemAbrir) { Start-Process $taskUrl }
