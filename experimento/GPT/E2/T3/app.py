import os
import re
import secrets
import sqlite3
from datetime import timedelta
from functools import wraps
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
            g.db.execute("PRAGMA foreign_keys = ON")
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
            db.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY,
                    author_id INTEGER NOT NULL REFERENCES users(id),
                    content TEXT NOT NULL CHECK(length(trim(content)) BETWEEN 1 AND 2000),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                    author_id INTEGER NOT NULL REFERENCES users(id),
                    content TEXT NOT NULL CHECK(length(trim(content)) BETWEEN 1 AND 1000),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS comments_post_id ON comments(post_id)")

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

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def render_feed(error=None, content="", status=200,
                    comment_error=None, comment_content="", comment_post_id=None):
        posts = []
        comments = {}
        if g.user is not None:
            posts = get_db().execute("""
                SELECT p.id, p.author_id, p.content, p.created_at, u.username
                FROM posts AS p JOIN users AS u ON u.id = p.author_id
                ORDER BY p.created_at DESC, p.id DESC
            """).fetchall()
            rows = get_db().execute("""
                SELECT c.id, c.post_id, c.content, c.created_at, u.username
                FROM comments AS c JOIN users AS u ON u.id = c.author_id
                ORDER BY c.created_at ASC, c.id ASC
            """).fetchall()
            for comment in rows:
                comments.setdefault(comment["post_id"], []).append(comment)
        return render_template(
            "index.html", posts=posts, comments=comments, error=error, content=content,
            comment_error=comment_error, comment_content=comment_content,
            comment_post_id=comment_post_id,
        ), status

    def owned_post(post_id):
        post = get_db().execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            abort(404)
        if post["author_id"] != g.user["id"]:
            abort(403)
        return post

    @app.get("/")
    def index():
        return render_feed()

    @app.post("/postagens")
    @login_required
    def create_post():
        content = request.form.get("content", "").strip()
        if not 1 <= len(content) <= 2000:
            return render_feed("A postagem deve conter de 1 a 2000 caracteres.", content, 400)
        with get_db() as db:
            db.execute("INSERT INTO posts (author_id, content) VALUES (?, ?)",
                       (g.user["id"], content))
        return redirect(url_for("index"))

    @app.post("/postagens/<int:post_id>/comentarios")
    @login_required
    def create_comment(post_id):
        content = request.form.get("content", "").strip()
        with get_db() as db:
            # Mantém a verificação da postagem e a inserção na mesma transação.
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone() is None:
                abort(404)
            if not 1 <= len(content) <= 1000:
                return render_feed(
                    status=400,
                    comment_error="O comentário deve conter de 1 a 1000 caracteres.",
                    comment_content=content, comment_post_id=post_id,
                )
            db.execute(
                "INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)",
                (post_id, g.user["id"], content),
            )
        return redirect(url_for("index", _anchor=f"post-{post_id}"))

    @app.route("/postagens/<int:post_id>/editar", methods=["GET", "POST"])
    @login_required
    def edit_post(post_id):
        post = owned_post(post_id)
        content = post["content"]
        error = None
        if request.method == "POST":
            content = request.form.get("content", "").strip()
            if not 1 <= len(content) <= 2000:
                error = "A postagem deve conter de 1 a 2000 caracteres."
            else:
                with get_db() as db:
                    db.execute("UPDATE posts SET content = ? WHERE id = ? AND author_id = ?",
                               (content, post_id, g.user["id"]))
                return redirect(url_for("index"))
        return render_template("edit_post.html", content=content, error=error), 400 if error else 200

    @app.post("/postagens/<int:post_id>/excluir")
    @login_required
    def delete_post(post_id):
        owned_post(post_id)
        with get_db() as db:
            db.execute("DELETE FROM posts WHERE id = ? AND author_id = ?",
                       (post_id, g.user["id"]))
        return redirect(url_for("index"))

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
