import os
from datetime import timedelta
from functools import wraps
from pathlib import Path
import re
import secrets
import sqlite3
import warnings
from io import BytesIO

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from PIL import Image, ImageOps, UnidentifiedImageError


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=str(Path(app.instance_path) / "usuarios.sqlite3"),
        UPLOAD_FOLDER=str(Path(app.instance_path) / "uploads"),
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    uploads = Path(app.config["UPLOAD_FOLDER"])
    uploads.mkdir(parents=True, exist_ok=True)
    if not app.config["SECRET_KEY"]:
        key_file = Path(app.instance_path) / "session.key"
        try:
            with key_file.open("x", encoding="utf-8") as file:
                file.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config["SECRET_KEY"] = key_file.read_text(encoding="utf-8").strip()

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
            g.db.create_function("casefold", 1, str.casefold, deterministic=True)
        return g.db

    @app.teardown_appcontext
    def close_db(error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        db = get_db()
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content TEXT NOT NULL CHECK(length(trim(content)) BETWEEN 1 AND 5000),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS posts_author ON posts(author_id)")
        db.execute("""CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            content TEXT NOT NULL CHECK(length(trim(content)) BETWEEN 1 AND 2000),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS comments_post ON comments(post_id)")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
        if "profile_photo" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT")
        db.commit()

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        return session["csrf_token"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def load_user_and_check_csrf():
        if request.method == "POST":
            expected = session.get("csrf_token", "")
            received = request.form.get("csrf_token", "")
            if not expected or not secrets.compare_digest(expected.encode(), received.encode()):
                abort(400, description="Formulário inválido. Recarregue a página e tente novamente.")
        g.user = None
        user_id = session.get("user_id")
        if user_id is not None:
            g.user = get_db().execute(
                "SELECT id, username, profile_photo FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if g.user is None:
                session.clear()

    @app.after_request
    def prevent_page_cache(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                flash("Entre para acessar as postagens.")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def own_post(post_id):
        post = get_db().execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            abort(404, description="Postagem não encontrada.")
        if post["author_id"] != g.user["id"]:
            abort(403, description="Você só pode alterar ou excluir suas próprias postagens.")
        return post

    def normalize_photo(file):
        data = file.stream.read(5 * 1024 * 1024 + 1)
        if not data or len(data) > 5 * 1024 * 1024:
            raise ValueError("A imagem deve ter entre 1 byte e 5 MiB.")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(data)) as image:
                    if image.format not in {"JPEG", "PNG", "WEBP"}:
                        raise ValueError("Utilize uma imagem JPEG, PNG ou WebP.")
                    if max(image.size) > 8192 or image.width * image.height > 16_000_000:
                        raise ValueError("A imagem deve ter até 16 megapixels e 8192 pixels por lado.")
                    image.verify()
                with Image.open(BytesIO(data)) as image:
                    image.seek(0)
                    photo = ImageOps.exif_transpose(image).convert("RGB")
                    photo.thumbnail((256, 256), Image.Resampling.LANCZOS)
                    photo.info.clear()
                    output = BytesIO()
                    photo.save(output, format="PNG")
                    return output.getvalue()
        except (UnidentifiedImageError, OSError, SyntaxError,
                Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
            raise ValueError("O arquivo não é uma imagem válida ou excede os limites.") from error

    @app.route("/perfil", methods=["GET", "POST"])
    @login_required
    def profile():
        error = None
        if request.method == "POST":
            file = request.files.get("photo")
            if file is None or not file.filename:
                error = "Selecione uma imagem para enviar."
            else:
                try:
                    data = normalize_photo(file)
                except ValueError as invalid:
                    error = str(invalid)
                else:
                    filename = secrets.token_hex(32) + ".png"
                    target = uploads / filename
                    try:
                        with target.open("xb") as output:
                            output.write(data)
                        with get_db() as db:
                            db.execute("BEGIN IMMEDIATE")
                            old = db.execute(
                                "SELECT profile_photo FROM users WHERE id = ?", (g.user["id"],)
                            ).fetchone()["profile_photo"]
                            db.execute("UPDATE users SET profile_photo = ? WHERE id = ?",
                                       (filename, g.user["id"]))
                    except Exception:
                        target.unlink(missing_ok=True)
                        raise
                    if old and re.fullmatch(r"[a-f0-9]{64}\.png", old):
                        try:
                            (uploads / old).unlink(missing_ok=True)
                        except OSError:
                            app.logger.warning("Não foi possível remover a foto anterior.")
                    flash("Foto de perfil atualizada.")
                    return redirect(url_for("profile"))
        return render_template("profile.html", error=error), 400 if error else 200

    @app.get("/usuarios/<int:user_id>/foto")
    @login_required
    def profile_photo(user_id):
        user = get_db().execute(
            "SELECT profile_photo FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None or not user["profile_photo"]:
            abort(404, description="Foto de perfil não encontrada.")
        filename = user["profile_photo"]
        if not re.fullmatch(r"[a-f0-9]{64}\.png", filename):
            abort(404)
        try:
            data = (uploads / filename).read_bytes()
        except FileNotFoundError:
            abort(404, description="Foto de perfil não encontrada.")
        return app.response_class(data, mimetype="image/png")

    @app.get("/")
    def index():
        posts = []
        comments = {}
        if g.user:
            posts = get_db().execute("""
                SELECT posts.*, users.username FROM posts
                JOIN users ON users.id = posts.author_id
                ORDER BY posts.created_at DESC, posts.id DESC
            """).fetchall()
            rows = get_db().execute("""
                SELECT comments.*, users.username FROM comments
                JOIN users ON users.id = comments.author_id
                ORDER BY comments.created_at, comments.id
            """).fetchall()
            for comment in rows:
                comments.setdefault(comment["post_id"], []).append(comment)
        return render_template("index.html", posts=posts, comments=comments)

    @app.get("/busca")
    @login_required
    def search():
        term = request.args.get("q", "").strip()
        users, posts = [], []
        error = None
        if not term:
            error = "Informe um termo para pesquisar."
        elif len(term) > 100 or "\x00" in term:
            error = "Use um termo válido com até 100 caracteres."
        else:
            db = get_db()
            users = db.execute("""
                SELECT id, username FROM users
                WHERE instr(casefold(username), casefold(?)) > 0
                ORDER BY username COLLATE NOCASE, id
            """, (term,)).fetchall()
            posts = db.execute("""
                SELECT posts.*, users.username FROM posts
                JOIN users ON users.id = posts.author_id
                WHERE instr(casefold(posts.content), casefold(?)) > 0
                ORDER BY posts.created_at DESC, posts.id DESC
            """, (term,)).fetchall()
        return render_template("search.html", term=term, users=users, posts=posts, error=error)

    @app.post("/postagens/<int:post_id>/comentarios")
    @login_required
    def add_comment(post_id):
        db = get_db()
        if db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone() is None:
            abort(404, description="Postagem não encontrada.")
        content = request.form.get("content", "").strip()
        if not 1 <= len(content) <= 2000 or "\x00" in content:
            flash("O comentário deve ter de 1 a 2000 caracteres válidos e não pode conter apenas espaços.")
        else:
            db.execute("INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)",
                       (post_id, g.user["id"], content))
            db.commit()
            flash("Comentário adicionado.")
        return redirect(url_for("index", _anchor=f"post-{post_id}"))

    @app.route("/postagens/nova", methods=["GET", "POST"])
    @login_required
    def create_post():
        content = request.form.get("content", "")
        if request.method == "POST":
            content = content.strip()
            if not 1 <= len(content) <= 5000 or "\x00" in content:
                flash("Use de 1 a 5000 caracteres. A postagem não pode conter apenas espaços.")
            else:
                db = get_db()
                db.execute("INSERT INTO posts (author_id, content) VALUES (?, ?)",
                           (g.user["id"], content))
                db.commit()
                flash("Postagem publicada.")
                return redirect(url_for("index"))
        return render_template("post_form.html", editing=False, content=content)

    @app.route("/postagens/<int:post_id>/editar", methods=["GET", "POST"])
    @login_required
    def edit_post(post_id):
        post = own_post(post_id)
        content = request.form.get("content", post["content"])
        if request.method == "POST":
            content = content.strip()
            if not 1 <= len(content) <= 5000 or "\x00" in content:
                flash("Use de 1 a 5000 caracteres. A postagem não pode conter apenas espaços.")
            else:
                db = get_db()
                db.execute("UPDATE posts SET content = ? WHERE id = ? AND author_id = ?",
                           (content, post_id, g.user["id"]))
                db.commit()
                flash("Postagem atualizada.")
                return redirect(url_for("index"))
        return render_template("post_form.html", editing=True, content=content)

    @app.post("/postagens/<int:post_id>/excluir")
    @login_required
    def delete_post(post_id):
        own_post(post_id)
        db = get_db()
        db.execute("DELETE FROM posts WHERE id = ? AND author_id = ?",
                   (post_id, g.user["id"]))
        db.commit()
        flash("Postagem excluída.")
        return redirect(url_for("index"))

    def error_page(error):
        if error.code == 413:
            error.description = "Envio muito grande. A foto deve ter até 5 MiB."
        return render_template("error.html", error=error), error.code

    for code in (400, 403, 404, 405, 413):
        app.register_error_handler(code, error_page)

    @app.route("/cadastro", methods=["GET", "POST"])
    def register():
        if g.user:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
                flash("Use de 3 a 30 letras sem acentos, números ou sublinhado no usuário.")
            elif not 8 <= len(password) <= 128 or password.isspace():
                flash("A senha deve ter de 8 a 128 caracteres e não pode conter apenas espaços.")
            else:
                db = get_db()
                try:
                    db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, generate_password_hash(password)),
                    )
                    db.commit()
                except sqlite3.IntegrityError:
                    db.rollback()
                    flash("Este nome de usuário já está cadastrado.")
                else:
                    flash("Cadastro realizado. Entre com seu usuário e senha.")
                    return redirect(url_for("login"))
        return render_template("auth.html", registering=True)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            if user and len(password) <= 128 and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session.permanent = True
                return redirect(url_for("index"))
            flash("Usuário ou senha inválidos.")
        return render_template("auth.html", registering=False)

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
