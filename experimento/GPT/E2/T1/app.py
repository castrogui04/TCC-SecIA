import os
import re
import secrets
import sqlite3
from datetime import timedelta
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=str(Path(app.instance_path) / "users.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config.get("SECRET_KEY"):
        key = os.environ.get("SECRET_KEY")
        if not key:
            key_file = Path(app.instance_path) / "secret.key"
            try:
                with key_file.open("x", encoding="utf-8") as file:
                    file.write(secrets.token_hex(32))
            except FileExistsError:
                pass
            key = key_file.read_text(encoding="utf-8").strip()
        app.config["SECRET_KEY"] = key

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        with get_db() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL
                )
            """)

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def load_user_and_check_csrf():
        g.user = None
        if request.method == "POST":
            token = request.form.get("csrf_token", "")
            if not secrets.compare_digest(token, session.get("csrf_token", "")) or not token:
                abort(400, description="Formulário expirado. Recarregue a página e tente novamente.")
        user_id = session.get("user_id")
        if user_id is not None:
            g.user = get_db().execute(
                "SELECT id, username FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if g.user is None:
                session.clear()

    @app.after_request
    def prevent_cached_pages(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.route("/cadastro", methods=["GET", "POST"])
    def register():
        if g.user:
            return redirect(url_for("index"))
        error = None
        username = ""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
                error = "Use de 3 a 30 letras sem acentos, números ou sublinhado no nome."
            elif not 8 <= len(password) <= 128:
                error = "A senha deve conter de 8 a 128 caracteres."
            else:
                try:
                    with get_db() as db:
                        db.execute(
                            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                            (username, generate_password_hash(password)),
                        )
                except sqlite3.IntegrityError:
                    error = "Este nome de usuário já está cadastrado."
                else:
                    return redirect(url_for("login", registered="1"))
        return render_template("auth.html", registering=True, error=error, username=username)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("index"))
        error = None
        username = ""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            if not 8 <= len(password) <= 128 or user is None or not check_password_hash(user["password_hash"], password):
                error = "Usuário ou senha inválidos."
            else:
                session.clear()
                session["user_id"] = user["id"]
                session.permanent = True
                return redirect(url_for("index"))
        return render_template("auth.html", registering=False, error=error, username=username)

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
