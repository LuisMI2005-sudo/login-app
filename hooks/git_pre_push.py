"""Entrada del hook nativo: reutiliza las mismas comprobaciones del agente."""
import sys
from guardian import run_tests

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
result = run_tests("PUSH BLOQUEADO POR PRE-PUSH")
if result == 0:
    print("Hook pre-push: 5 tests aprobados. Se permite el push.", file=sys.stderr)
sys.exit(result)
