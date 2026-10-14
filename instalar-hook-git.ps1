$ErrorActionPreference = 'Stop'
$hookDirectory = & git -C $PSScriptRoot rev-parse --path-format=absolute --git-path hooks
if ($LASTEXITCODE -ne 0) { throw 'Primero inicializa el repositorio Git del login.' }
$destination = Join-Path $hookDirectory 'pre-push'
if (Test-Path -LiteralPath $destination) { throw 'Ya existe un hook pre-push; no se sobrescribió.' }
Copy-Item -LiteralPath "$PSScriptRoot/hooks/pre-push" -Destination $destination
Write-Host "Hook nativo instalado: $destination"
