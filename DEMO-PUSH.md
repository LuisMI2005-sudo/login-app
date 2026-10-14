# Demostración del push y los cinco tests

Repositorio: https://github.com/LuisMI2005-sudo/login-app

1. Se hizo el push inicial directo del commit `761eeed`, manteniendo un `self.fail()`
   intencional. GitHub Actions confirmó el fallo:
   https://github.com/LuisMI2005-sudo/login-app/actions/runs/38612720330
2. Se instalaron y confirmaron los scripts del hook nativo pre-push en `4ca7d32`.
3. Se intentó un nuevo `git push origin main`. El hook ejecutó cinco tests y lo bloqueó
   con `PUSH BLOQUEADO POR PRE-PUSH` y `FAILED (failures=1)`; los commits no se enviaron.
4. Con autorización del usuario se reemplazó la prueba artificial por un test real del
   límite de intentos. La suite conserva exactamente cinco tests.
5. El siguiente push debe ejecutar el mismo hook, aprobar las cinco pruebas y publicar
   la corrección. Actions vuelve a ejecutar la suite en GitHub.

El hook comprueba y bloquea; no edita código ni pruebas por su cuenta.
La versión inicial roja se conserva en el historial para la presentación.
