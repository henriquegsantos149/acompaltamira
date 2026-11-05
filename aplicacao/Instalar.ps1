$ErrorActionPreference='Stop'
$backendRoot=Join-Path $PSScriptRoot 'backend'
$frontendRoot=Join-Path $PSScriptRoot 'frontend'
$venvRoot=Join-Path $backendRoot '.venv'
if (-not (Test-Path -LiteralPath (Join-Path $venvRoot 'Scripts/python.exe'))) {
    python -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o ambiente Python.' }
}
& (Join-Path $venvRoot 'Scripts/python.exe') -m pip install -r (Join-Path $backendRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'A instalação Python falhou.' }
Push-Location $frontendRoot
try {
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'A instalação da interface falhou.' }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'A compilação da interface falhou.' }
} finally { Pop-Location }
Write-Host 'Instalação concluída. Execute Iniciar.ps1 para abrir o painel.'
