import re
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import check_password_hash
from app import create_app


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = str(Path(self.temp.name) / "usuarios.db")
        self.config = {"TESTING": True, "DATABASE": self.database, "SECRET_KEY": "clave-solo-para-pruebas"}
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def post(self, path, data=None):
        page = self.client.get("/login" if path == "/logout" else path)
        if path == "/logout":
            page = self.client.get("/cuenta")
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True)).group(1)
        return self.client.post(path, data={**(data or {}), "csrf_token": token}, follow_redirects=True)

    def register(self, **changes):
        return self.post("/registro", {"nombre": "Ana Demo", "email": "ana@example.com",
                                      "password": "ClaveDemo2026!", "confirm_password": "ClaveDemo2026!", **changes})

    def login(self, **changes):
        return self.post("/login", {"email": "ana@example.com", "password": "ClaveDemo2026!", **changes})

    def test_register_login_and_logout(self):
        self.assertIn("Tu cuenta está lista", self.register().get_data(as_text=True))
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hola, Ana Demo", response.get_data(as_text=True))
        self.assertIn("Cerraste tu sesión", self.post("/logout").get_data(as_text=True))
        self.assertEqual(self.client.get("/cuenta").status_code, 302)

    def test_private_page_and_wrong_credentials_are_rejected(self):
        response = self.client.get("/cuenta")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/login"))
        self.register()
        self.assertEqual(self.login(password="incorrecta").status_code, 401)
        self.assertEqual(self.login(email="' OR 1=1 --").status_code, 401)
        self.assertEqual(self.client.get("/cuenta").status_code, 302)

    def test_password_hash_and_database_survive_restart(self):
        self.register(email="ANA@EXAMPLE.COM")
        with closing(sqlite3.connect(self.database)) as connection:
            email, stored = connection.execute("SELECT email, password_hash FROM usuarios").fetchone()
        self.assertEqual(email, "ana@example.com")
        self.assertNotEqual(stored, "ClaveDemo2026!")
        self.assertTrue(check_password_hash(stored, "ClaveDemo2026!"))
        self.client = create_app(self.config).test_client()
        self.assertIn("Hola, Ana Demo", self.login().get_data(as_text=True))

    def test_validation_duplicate_email_and_csrf(self):
        for data in ({"password": "corta", "confirm_password": "corta"},
                     {"confirm_password": "otra-contraseña"}, {"email": "no-es-correo"}):
            with self.subTest(data=data):
                self.assertEqual(self.register(**data).status_code, 400)
        self.register()
        self.assertEqual(self.register(email="ANA@example.com").status_code, 400)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0], 1)
        self.client.get("/login")
        for token in ("", "incorrecto", "contraseña"):
            with self.subTest(token=token):
                self.assertEqual(self.client.post("/login", data={"csrf_token": token}).status_code, 400)
        self.assertEqual(self.client.get("/logout").status_code, 405)

    def test_demo_fallo_inicial_intencional(self):
        # Solicitado para el primer push de la demo. No es un defecto del login.
        self.fail("FALLO INTENCIONAL: primer push de la demostración. Pendiente de nuevas instrucciones.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
