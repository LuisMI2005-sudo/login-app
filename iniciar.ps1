$ErrorActionPreference = 'Stop'
$pythonApp = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonApp)) {
    & py -3 -m venv "$PSScriptRoot/.venv"
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno. Comprueba que Python esté instalado.' }
}
& $pythonApp -c 'import flask' 2>$null
if ($LASTEXITCODE -ne 0) {
    & $pythonApp -m pip install -r "$PSScriptRoot/requirements.txt"
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
}
Write-Host 'Abre http://127.0.0.1:5000 en tu navegador. Para detener: Ctrl+C.'
& $pythonApp "$PSScriptRoot/app.py"
exit $LASTEXITCODE
