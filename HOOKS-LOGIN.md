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

Se conservan exactamente 5 tests del login: cuatro deben aprobar y
`test_demo_fallo_inicial_intencional` falla expresamente. Ese fallo independiente del
login se mantiene para la demostración. El resultado esperado es:

```text
Ran 5 tests
FAILED (failures=1)
```

La configuración de Actions tampoco omite ni tolera ese fallo. Una vez que esta
carpeta sea la raíz de un repositorio y se suba, el workflow debe quedar rojo.
Los tests protegidos solo deben cambiarse con una instrucción explícita de la clase.

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

Los hooks son del agente. Los comandos ejecutados manualmente en tu terminal no son
interceptados por ellos. GitHub Actions valida el código después de recibir el push.
La base de datos, las claves, las bitácoras y el entorno virtual quedan fuera de Git.

Esta etapa prepara archivos y mantiene el fallo intencional. No inicia un repositorio,
no configura remotos y no publica nuevos commits.
