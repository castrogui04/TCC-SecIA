import os
import sqlite3
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuracao de upload de arquivos
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Limite de 5 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializa o banco de dados e cria tabelas se nao existirem
with app.app_context():
    init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Você precisa estar autenticado para realizar esta ação.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_current_user():
    user = None
    if "user_id" in session:
        conn = get_db_connection()
        user = conn.execute(
            "SELECT id, username, profile_pic FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        conn.close()
    return dict(current_user=user)

@app.route("/")
def index():
    user = None
    conn = get_db_connection()
    
    if "user_id" in session:
        user = conn.execute(
            "SELECT id, username, profile_pic FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()

    # Busca postagens unindo autor e sua foto de perfil
    posts_data = conn.execute("""
        SELECT p.id, p.content, p.created_at, p.user_id, u.username, u.profile_pic
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC, p.id DESC
    """).fetchall()

    posts = []
    for p in posts_data:
        comments = conn.execute("""
            SELECT c.id, c.content, c.created_at, c.user_id, u.username, u.profile_pic
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC, c.id ASC
        """, (p["id"],)).fetchall()
        
        posts.append({
            "id": p["id"],
            "content": p["content"],
            "created_at": p["created_at"],
            "user_id": p["user_id"],
            "username": p["username"],
            "profile_pic": p["profile_pic"],
            "comments": comments
        })
    
    conn.close()
    return render_template("index.html", user=user, posts=posts)

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Nome de usuário e senha são obrigatórios.", "danger")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            flash("Conta criada com sucesso! Faça login para continuar.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Este nome de usuário já está em uso.", "danger")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Bem-vindo de volta, {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Nome de usuário ou senha incorretos.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, username, profile_pic FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()

    if request.method == "POST":
        if "profile_pic" not in request.files:
            flash("Nenhum arquivo enviado.", "danger")
            conn.close()
            return redirect(url_for("profile"))

        file = request.files["profile_pic"]
        if file.filename == "":
            flash("Selecione uma imagem para enviar.", "danger")
            conn.close()
            return redirect(url_for("profile"))

        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            unique_filename = f"user_{session['user_id']}_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

            # Remove foto antiga se existir no disco
            if user["profile_pic"]:
                old_file = os.path.join(app.config["UPLOAD_FOLDER"], user["profile_pic"])
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except OSError:
                        pass

            file.save(filepath)

            conn.execute(
                "UPDATE users SET profile_pic = ? WHERE id = ?",
                (unique_filename, session["user_id"])
            )
            conn.commit()
            conn.close()

            flash("Foto de perfil atualizada com sucesso!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Formato de imagem inválido. Use PNG, JPG, JPEG, GIF ou WEBP.", "danger")

    conn.close()
    return render_template("profile.html", user=user)

@app.route("/posts/create", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content", "").strip()
    if not content:
        flash("A postagem não pode ser vazia.", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO posts (user_id, content) VALUES (?, ?)",
        (session["user_id"], content)
    )
    conn.commit()
    conn.close()

    flash("Publicação criada com sucesso!", "success")
    return redirect(url_for("index"))

@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    conn = get_db_connection()
    post = conn.execute(
        "SELECT * FROM posts WHERE id = ?", (post_id,)
    ).fetchone()

    if post is None:
        conn.close()
        abort(404)

    if post["user_id"] != session["user_id"]:
        conn.close()
        flash("Você não tem permissão para editar esta postagem.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if not content:
            flash("O conteúdo da postagem não pode ser vazio.", "danger")
            conn.close()
            return render_template("edit_post.html", post=post)

        conn.execute(
            "UPDATE posts SET content = ? WHERE id = ?",
            (content, post_id)
        )
        conn.commit()
        conn.close()

        flash("Postagem atualizada com sucesso!", "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("edit_post.html", post=post)

@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    conn = get_db_connection()
    post = conn.execute(
        "SELECT * FROM posts WHERE id = ?", (post_id,)
    ).fetchone()

    if post is None:
        conn.close()
        abort(404)

    if post["user_id"] != session["user_id"]:
        conn.close()
        flash("Você não tem permissão para excluir esta postagem.", "danger")
        return redirect(url_for("index"))

    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

    flash("Postagem excluída com sucesso!", "info")
    return redirect(url_for("index"))

@app.route("/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def add_comment(post_id):
    content = request.form.get("content", "").strip()
    if not content:
        flash("O comentário não pode ser vazio.", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    post = conn.execute(
        "SELECT id FROM posts WHERE id = ?", (post_id,)
    ).fetchone()

    if post is None:
        conn.close()
        abort(404)

    conn.execute(
        "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
        (post_id, session["user_id"], content)
    )
    conn.commit()
    conn.close()

    flash("Comentário adicionado!", "success")
    return redirect(url_for("index"))

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    users = []
    posts = []

    if query:
        search_pattern = f"%{query}%"
        conn = get_db_connection()

        # Busca usuarios com foto de perfil
        users = conn.execute(
            "SELECT id, username, profile_pic FROM users WHERE username LIKE ? ORDER BY username ASC",
            (search_pattern,)
        ).fetchall()

        # Busca postagens com autor e comentarios
        posts_data = conn.execute("""
            SELECT p.id, p.content, p.created_at, p.user_id, u.username, u.profile_pic
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.content LIKE ?
            ORDER BY p.created_at DESC, p.id DESC
        """, (search_pattern,)).fetchall()

        for p in posts_data:
            comments = conn.execute("""
                SELECT c.id, c.content, c.created_at, c.user_id, u.username, u.profile_pic
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.post_id = ?
                ORDER BY c.created_at ASC, c.id ASC
            """, (p["id"],)).fetchall()

            posts.append({
                "id": p["id"],
                "content": p["content"],
                "created_at": p["created_at"],
                "user_id": p["user_id"],
                "username": p["username"],
                "profile_pic": p["profile_pic"],
                "comments": comments
            })

        conn.close()

    return render_template("search.html", query=query, users=users, posts=posts)

if __name__ == "__main__":
    app.run(debug=True)
