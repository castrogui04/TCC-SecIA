import os
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path
from functools import wraps

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    DATABASE=Path(app.instance_path) / "users.sqlite3",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=128 * 1024,
)


def connect_db():
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    database = Path(app.config["DATABASE"])
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_db()) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                content TEXT NOT NULL CHECK(length(trim(content)) BETWEEN 1 AND 5000)
            )
        """)


@app.before_request
def load_user():
    with closing(connect_db()) as db:
        g.user = db.execute(
            "SELECT id, username FROM users WHERE id = ?", (session.get("user_id"),)
        ).fetchone()
    if g.user is None:
        session.pop("user_id", None)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login"), code=303)
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def form_context():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return {"csrf_token": session["csrf_token"]}


@app.before_request
def validate_form_token():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        received = request.form.get("csrf_token", "").encode("utf-8")
        if not expected or not secrets.compare_digest(expected.encode("ascii"), received):
            abort(400, description="Formulário inválido. Recarregue a página e tente novamente.")


@app.get("/")
def index():
    posts = []
    if g.user is not None:
        with closing(connect_db()) as db:
            posts = db.execute(
                "SELECT posts.id, posts.user_id, posts.content, users.username "
                "FROM posts JOIN users ON users.id = posts.user_id ORDER BY posts.id DESC"
            ).fetchall()
    return render_template("index.html", posts=posts)


@app.post("/postagens")
@login_required
def create_post():
    content = request.form.get("content", "").strip()
    if not 1 <= len(content) <= 5000:
        return render_template("post.html", content=content, post=None), 400
    with closing(connect_db()) as db, db:
        db.execute(
            "INSERT INTO posts (user_id, content) VALUES (?, ?)", (g.user["id"], content)
        )
    return redirect(url_for("index"), code=303)


def own_post(db, post_id):
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)
    if post["user_id"] != g.user["id"]:
        abort(403)
    return post


@app.route("/postagens/<int:post_id>/editar", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    with closing(connect_db()) as db, db:
        post = own_post(db, post_id)
        if request.method == "GET":
            return render_template("post.html", post=post, content=post["content"])
        content = request.form.get("content", "").strip()
        if not 1 <= len(content) <= 5000:
            return render_template("post.html", post=post, content=content), 400
        db.execute(
            "UPDATE posts SET content = ? WHERE id = ? AND user_id = ?",
            (content, post_id, g.user["id"]),
        )
    return redirect(url_for("index"), code=303)


@app.post("/postagens/<int:post_id>/excluir")
@login_required
def delete_post(post_id):
    with closing(connect_db()) as db, db:
        own_post(db, post_id)
        db.execute(
            "DELETE FROM posts WHERE id = ? AND user_id = ?", (post_id, g.user["id"])
        )
    return redirect(url_for("index"), code=303)


@app.route("/cadastro", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("index.html", mode="register")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not 1 <= len(username) <= 50 or not 8 <= len(password) <= 128:
        flash("Informe um usuário de 1 a 50 caracteres e uma senha de 8 a 128 caracteres.")
        return render_template("index.html", mode="register", entered_name=username), 400

    password_hash = generate_password_hash(password)
    with closing(connect_db()) as db, db:
        result = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?) "
            "ON CONFLICT(username) DO NOTHING",
            (username, password_hash),
        )
        created = result.rowcount == 1

    if not created:
        flash("Este nome de usuário já está em uso.")
        return render_template("index.html", mode="register", entered_name=username), 409

    flash("Cadastro realizado. Entre com seu usuário e senha.")
    return redirect(url_for("login"), code=303)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("index.html", mode="login")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    with closing(connect_db()) as db:
        user = db.execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()

    if user is None or not 8 <= len(password) <= 128 or not check_password_hash(user[1], password):
        flash("Usuário ou senha inválidos.")
        return render_template("index.html", mode="login", entered_name=username), 401

    session.clear()
    session["user_id"] = user[0]
    return redirect(url_for("index"), code=303)


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"), code=303)


init_db()

if __name__ == "__main__":
    app.run()
