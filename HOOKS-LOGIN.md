# Hooks y Actions del login

Adaptación del proyecto `hooks` de esta práctica. Todos los controles ejecutan los
tests de este login; no dependen de `proyecto-demo` ni de la carpeta de ejemplo.

## Archivos

- `.codex/hooks.json` y `.codex/hooks/*.py`: registro y entradas para Codex.
- `.claude/settings.json` y `.claude/hooks/*.py`: registro y entradas para Claude Code.
- `hooks/guardian.py`: lógica compartida de protección, bloqueo, pruebas y auditoría.
- `hooks/configurar.py`: genera las rutas de los scripts para el equipo actual.
- `.github/workflows/tests.yml`: ejecuta los 5 tests en GitHub Actions.

## Controles adaptados

1. `PreToolUse`: protege `tests/`, `.env*` e `instance/` durante ediciones del agente.
2. `PreToolUse`: bloquea los comandos peligrosos del ejemplo y comprueba los 5 tests
   antes de permitir un `git push` pedido al agente. Si alguno falla, devuelve código 2.
3. `PostToolUse`: después de editar un archivo Python, ejecuta los 5 tests y reporta
   los fallos. La edición ya realizada no se revierte automáticamente.
4. `PostToolUse` y `SubagentStop`: registra eventos en la bitácora del agente.

No se repite dos veces la validación previa al push, como sucedía en uno de los scripts
del ejemplo. Las rutas Windows se generan con comillas para la carpeta con espacios.

## Estado de los tests

Se conservan exactamente **5 tests funcionales** y ahora deben aprobar todos.
La prueba de fallo intencional del primer commit se reemplazó, con autorización del
usuario, por una comprobación real del límite de intentos de login.

```text
Ran 5 tests
OK
```

## Hook nativo de Git

`hooks/pre-push` y `hooks/git_pre_push.py` reutilizan la misma validación de cinco
tests. Esta copia lo tiene instalado en `.git/hooks/pre-push`: un `git push` normal
también se bloquea si las pruebas fallan. El hook informa el problema; la corrección
del código o de una prueba autorizada la realiza el desarrollador o el agente.

En una copia recién clonada se instala una vez con:

```powershell
.\instalar-hook-git.ps1
```

Las definiciones de Codex y Claude son independientes y requieren activación en el
agente. El hook nativo se ejecuta directamente desde Git, incluso en una terminal.

## Uso en Windows

Desde esta carpeta:

```powershell
.\configurar-hooks.ps1
.\iniciar-codex.ps1
```

En Codex, revisa la confianza del proyecto y las definiciones mediante `/hooks`.
Que existan los archivos no significa que estén activos en una sesión ya abierta.
Si mueves la carpeta, vuelve a ejecutar `configurar-hooks.ps1` para regenerar las rutas.

Para comprobar los tests directamente:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

GitHub Actions valida el código después de recibir el push. La base de datos,
las claves, las bitácoras y el entorno virtual quedan fuera de Git.

El repositorio público es https://github.com/LuisMI2005-sudo/login-app.
Consulta DEMO-PUSH.md para la ejecución inicial roja y el bloqueo demostrado.
