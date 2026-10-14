$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath "$PSScriptRoot/.codex/hooks.json")) {
    throw 'Primero ejecuta configurar-hooks.ps1.'
}
& codex -C $PSScriptRoot @args
exit $LASTEXITCODE
