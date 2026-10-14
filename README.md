# Login con base de datos

Aplicación local para registrar usuarios, iniciar sesión, acceder a un panel privado y
cerrar sesión. Está construida con Flask y SQLite; no requiere MySQL ni otro servidor
de base de datos. Cada registro queda guardado al cerrar y volver a abrir la aplicación.

## Iniciar en Visual Studio Code

Abre una terminal PowerShell y ejecuta:

```powershell
cd C:\Users\HP\Practica clase 14\login-app
.\iniciar.ps1
```

La primera vez el script prepara un entorno virtual e instala Flask. Luego abre
[http://127.0.0.1:5000](http://127.0.0.1:5000) en el navegador. El servidor permanece
en esa terminal; para detenerlo pulsa Ctrl+C.

Selecciona **Crea una cuenta**, registra tu nombre, correo y una contraseña de al menos
8 caracteres. Después inicia sesión con esos datos. No hay cuentas ni contraseñas
predeterminadas. En el panel puedes consultar tu perfil y cerrar sesión.

Si el puerto 5000 ya está ocupado:

```powershell
$env:PORT = '5001'
.\iniciar.ps1
```

En ese caso abre http://127.0.0.1:5001.

## Base de datos

El primer arranque crea automáticamente `instance/usuarios.db`, con las tablas
`usuarios` e `intentos`. El esquema está en `schema.sql`.

- `usuarios`: id, nombre, email único, hash de contraseña y fecha de creación (UTC).
- `intentos`: control temporal de intentos de entrada por correo y dirección de origen.

Para ver los registros puedes abrir `usuarios.db` con un visor SQLite. Los archivos
de `instance/` y `.venv/` están excluidos de Git. `instance/session.key` conserva la
clave con que se firman las sesiones. No compartas esa carpeta ni la subas al repo.

## Verificar

Desde `login-app`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Las pruebas usan una base de datos temporal. Comprueban registro, acceso privado,
contraseñas con hash, correos duplicados, validación, consultas parametrizadas,
protección CSRF y persistencia. Esta entrega contiene exactamente **5 tests**:
cuatro funcionales y `test_demo_fallo_inicial_intencional`, que falla expresamente para
que el primer push muestre una ejecución roja en Actions. Ese fallo fue solicitado
para la demostración y no afecta el uso del login. Queda pendiente de las siguientes
instrucciones; por ahora la ejecución esperada es `Ran 5 tests` y `FAILED (failures=1)`.

## Archivos

`app.py` contiene las rutas y la autenticación; `schema.sql` define las tablas;
`templates/` y `static/` contienen la interfaz. La app se mantiene separada de
`proyecto-demo` y sus pruebas existentes.

El servidor de `iniciar.ps1` está destinado a la demostración local. Para publicar
en Internet se requiere un servidor de producción con HTTPS y activar
`LOGIN_COOKIE_SECURE=1`. Esta versión no incluye recuperación por correo ni verificación
de direcciones de email.

Referencia: [autenticación y SQLite en Flask](https://flask.palletsprojects.com/en/stable/tutorial/views/).

## Hooks y workflow propios

Consulta [HOOKS-LOGIN.md](HOOKS-LOGIN.md) para los hooks de Codex y Claude y el workflow de GitHub Actions. La configuración está preparada para esta carpeta como raíz del proyecto.
