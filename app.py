"""Login local con Flask, usuarios persistentes en SQLite y sesiones firmadas."""
from datetime import timedelta
import hashlib
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=str(Path(app.instance_path) / "usuarios.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("LOGIN_COOKIE_SECURE") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        instance = Path(app.instance_path)
        instance.mkdir(parents=True, exist_ok=True)
        secret_file = instance / "session.key"
        if not secret_file.exists():
            try:
                with secret_file.open("x", encoding="utf-8") as f:
                    f.write(secrets.token_hex(32))
            except FileExistsError:
                pass
        app.config["SECRET_KEY"] = secret_file.read_text(encoding="utf-8").strip()

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(error=None):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    with app.app_context():
        Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
        db().executescript((Path(app.root_path) / "schema.sql").read_text(encoding="utf-8"))
        db().commit()

    dummy_hash = generate_password_hash(secrets.token_urlsafe(24))

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def load_user_and_check_csrf():
        g.user = None
        if session.get("user_id") is not None:
            g.user = db().execute(
                "SELECT id, nombre, email, creado_en FROM usuarios WHERE id = ?",
                (session["user_id"],),
            ).fetchone()
            if g.user is None:
                session.clear()
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            supplied = request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected.encode(), supplied.encode()):
                return render_template("error.html", message="La sesión del formulario venció. Vuelve a intentarlo."), 400

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return redirect(url_for("dashboard" if g.user else "login"))

    @app.route("/registro", methods=["GET", "POST"])
    def register():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("nombre", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            error = None
            if not 2 <= len(name) <= 80:
                error = "Escribe un nombre de entre 2 y 80 caracteres."
            elif len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                error = "Escribe un correo electrónico válido."
            elif not 8 <= len(password) <= 128:
                error = "Tu contraseña debe tener entre 8 y 128 caracteres."
            elif password != confirm:
                error = "Las contraseñas no coinciden."
            if error is None:
                try:
                    db().execute(
                        "INSERT INTO usuarios (nombre, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password)),
                    )
                    db().commit()
                except sqlite3.IntegrityError:
                    db().rollback()
                    error = "Ya existe una cuenta con ese correo. Inicia sesión."
                else:
                    session.clear()
                    flash("Tu cuenta está lista. Ahora puedes iniciar sesión.", "success")
                    return redirect(url_for("login"))
            flash(error, "error")
            return render_template("auth.html", mode="register"), 400
        return render_template("auth.html", mode="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()[:254]
            password = request.form.get("password", "")
            attempt_key = hashlib.sha256(f"{request.remote_addr}|{email}".encode()).hexdigest()
            now = int(time.time())
            attempts = db().execute("SELECT * FROM intentos WHERE clave = ?", (attempt_key,)).fetchone()
            if attempts and now - attempts["inicio"] < 900 and attempts["fallos"] >= 5:
                flash("Demasiados intentos. Espera 15 minutos antes de intentarlo de nuevo.", "error")
                return render_template("auth.html", mode="login"), 429
            user = db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
            valid = False
            if len(password) <= 128:
                valid = check_password_hash(user["password_hash"] if user else dummy_hash, password)
            if not user or not valid:
                if not attempts or now - attempts["inicio"] >= 900:
                    db().execute("INSERT OR REPLACE INTO intentos (clave, fallos, inicio) VALUES (?, 1, ?)", (attempt_key, now))
                else:
                    db().execute("UPDATE intentos SET fallos = fallos + 1 WHERE clave = ?", (attempt_key,))
                db().execute("DELETE FROM intentos WHERE inicio < ?", (now - 900,))
                db().commit()
                flash("El correo o la contraseña no son correctos.", "error")
                return render_template("auth.html", mode="login"), 401
            db().execute("DELETE FROM intentos WHERE clave = ?", (attempt_key,))
            db().commit()
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = True
            return redirect(url_for("dashboard"))
        return render_template("auth.html", mode="login")

    @app.get("/cuenta")
    def dashboard():
        if not g.user:
            return redirect(url_for("login"))
        return render_template("dashboard.html")

    @app.post("/logout")
    def logout():
        session.clear()
        flash("Cerraste tu sesión correctamente.", "success")
        return redirect(url_for("login"))

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
