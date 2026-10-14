$ErrorActionPreference = 'Stop'
$pythonLogin = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonLogin)) { throw 'Primero prepara el entorno con iniciar.ps1.' }
& $pythonLogin -B "$PSScriptRoot/hooks/configurar.py"
exit $LASTEXITCODE
