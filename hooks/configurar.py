"""Genera rutas válidas para este equipo, incluso si la carpeta tiene espacios."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
python = ROOT / ".venv" / "Scripts" / "python.exe" if sys.platform == "win32" else ROOT / ".venv" / "bin" / "python"
if not python.is_file():
    raise SystemExit("Falta el entorno .venv. Ejecuta iniciar.ps1 para prepararlo antes de configurar los hooks.")

files = {"proteger_archivos": "protect", "bloquear_comandos": "commands",
         "ejecutar_tests": "tests", "auditoria": "audit"}
for provider in (".codex", ".claude"):
    directory = ROOT / provider / "hooks"
    directory.mkdir(parents=True, exist_ok=True)
    for filename, mode in files.items():
        script = f'''from pathlib import Path
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
from guardian import main
sys.exit(main("{mode}", "{provider}"))
'''
        (directory / f"{filename}.py").write_text(script, encoding="utf-8")

    def handler(filename, timeout=10):
        script = (directory / f"{filename}.py").as_posix()
        command = f'"{python.as_posix()}" -B "{script}"'
        result = {"type": "command", "command": command, "timeout": timeout}
        if provider == ".codex" and sys.platform == "win32":
            result["commandWindows"] = f'& {command}'
        return result

    edits = "apply_patch" if provider == ".codex" else "Edit|Write"
    shell = "Bash" if provider == ".codex" else "Bash|PowerShell"
    config = {"hooks": {
        "PreToolUse": [
            {"matcher": edits, "hooks": [handler("proteger_archivos")]},
            {"matcher": shell, "hooks": [handler("bloquear_comandos", 60)]},
        ],
        "PostToolUse": [
            {"matcher": edits, "hooks": [handler("ejecutar_tests", 60)]},
            {"matcher": "*", "hooks": [handler("auditoria")]},
        ],
        "SubagentStop": [{"hooks": [handler("auditoria")]}],
    }}
    target = ROOT / provider / ("hooks.json" if provider == ".codex" else "settings.json")
    target.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("Configurados los hooks de Codex y Claude para:", ROOT)
