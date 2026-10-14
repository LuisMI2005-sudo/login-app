"""Controles del login adaptados de la demo de hooks de la clase."""
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    r"\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r": "borrado recursivo forzado",
    r"Remove-Item\b.*-Recurse": "borrado recursivo en PowerShell",
    r"\bgit(?:\.exe)?\b[^\r\n;&|]*\bpush\b.*(?:--force|-f\b)": "push forzado",
    r"\bgit(?:\.exe)?\b[^\r\n;&|]*\breset\s+--hard": "reset destructivo",
    r"DROP\s+(TABLE|DATABASE)": "eliminar tablas o bases de datos",
    r"\bdel\s+/[sq]": "borrado masivo en Windows",
}


def paths_from(data):
    tool_input = data.get("tool_input") or {}
    paths = [tool_input.get(key) for key in ("file_path", "filePath", "path") if tool_input.get(key)]
    patch = tool_input.get("command") or tool_input.get("patch") or ""
    if isinstance(patch, str):
        paths.extend(re.findall(r"^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$", patch, re.MULTILINE))
    return [str(path).strip().replace("\\", "/") for path in paths]


def protect(data):
    for path in paths_from(data):
        parts = path.lower().split("/")
        if "tests" in parts[:-1]:
            print(f"BLOQUEADO por hook: la prueba '{path}' está protegida.", file=sys.stderr)
            return 2
        if parts[-1].startswith(".env") or "instance" in parts[:-1]:
            print(f"BLOQUEADO por hook: '{path}' es un archivo privado del login.", file=sys.stderr)
            return 2
    return 0


def run_tests(context="PRUEBAS"):
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=50,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"{context}: no se pudieron ejecutar los tests: {error}", file=sys.stderr)
        return 2
    report = result.stdout + result.stderr
    count = re.search(r"Ran (\d+) tests?\b", report)
    if result.returncode != 0 or not count or int(count[1]) != 5:
        print(f"{context}: deben aprobar exactamente 5 tests del login.\n" + report[-6000:], file=sys.stderr)
        return 2
    return 0


def block_commands(data):
    tool_input = data.get("tool_input") or {}
    command = str(tool_input.get("command") or tool_input.get("cmd") or "")
    for pattern, reason in PATTERNS.items():
        if re.search(pattern, command, re.IGNORECASE):
            print(f"BLOQUEADO por hook: {reason}.", file=sys.stderr)
            return 2
    if re.search(r"\bgit(?:\.exe)?\b[^\r\n;&|]*\bpush\b", command, re.IGNORECASE):
        return run_tests("PUSH BLOQUEADO")
    return 0


def post_tests(data):
    if not any(path.lower().endswith(".py") for path in paths_from(data)):
        return 0
    result = run_tests("HOOK POSTERIOR")
    if result == 0:
        print(json.dumps({"systemMessage": "Hook del login: 5 tests aprobados.",
                          "hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                 "additionalContext": "Los 5 tests del login pasaron."}}))
    return result


def audit(data, provider):
    event = str(data.get("hook_event_name", "?"))
    action = "SUBAGENTE terminó" if event == "SubagentStop" else str(data.get("tool_name", "?"))
    paths = paths_from(data)
    # Se registran rutas, nunca el comando completo ni argumentos con contraseñas.
    detail = ", ".join(paths).replace("\n", " ").replace("\r", " ")[:150]
    log = ROOT / provider / "auditoria.log"
    with log.open("a", encoding="utf-8") as file:
        file.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {event} | {action} | {detail}\n")
    return 0


def main(mode, provider):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        if not isinstance(data, dict) or not isinstance(data.get("tool_input", {}), (dict, type(None))):
            raise ValueError("La entrada del hook debe ser un objeto JSON.")
        operations = {"protect": protect, "commands": block_commands, "tests": post_tests}
        return audit(data, provider) if mode == "audit" else operations[mode](data)
    except (ValueError, KeyError, OSError) as error:
        print(f"Error del hook del login: {error}", file=sys.stderr)
        return 1
