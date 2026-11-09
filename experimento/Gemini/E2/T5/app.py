import sqlite3
import os
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chave_secreta_padrao_para_desenvolvimento_12345")
DATABASE = "database.db"

# Configurações de upload
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "avatars")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Limite máximo de 5MB por arquivo

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    conn = get_db()
    with app.open_resource("schema.sql", mode="r") as f:
        conn.cursor().executescript(f.read())
    
    # Migração defensiva: adiciona coluna profile_pic caso a tabela users já exista de versão anterior
    columns = [col["name"] for col in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "profile_pic" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT NULL")
        
    conn.commit()
    conn.close()

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Você precisa estar conectado para acessar esta página.", "danger")
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view

@app.context_processor
def inject_current_user():
    current_user = None
    if "user_id" in session:
        conn = get_db()
        current_user = conn.execute(
            "SELECT id, username, profile_pic FROM users WHERE id = ?", 
            (session["user_id"],)
        ).fetchone()
        conn.close()
    return dict(current_user=current_user)

def get_post(post_id, check_author=True):
    conn = get_db()
    post = conn.execute(
        """
        SELECT p.id, p.content, p.created_at, p.updated_at, p.author_id, u.username, u.profile_pic
        FROM posts p
        JOIN users u ON p.author_id = u.id
        WHERE p.id = ?
        """,
        (post_id,)
    ).fetchone()
    conn.close()

    if post is None:
        abort(404, f"Postagem de ID {post_id} não foi encontrada.")

    if check_author and post["author_id"] != session.get("user_id"):
        abort(403, "Você não tem permissão para alterar ou excluir esta postagem.")

    return post

@app.route("/")
def index():
    user = None
    conn = get_db()
    if "user_id" in session:
        user = conn.execute(
            "SELECT id, username, profile_pic FROM users WHERE id = ?", 
            (session["user_id"],)
        ).fetchone()

    posts_rows = conn.execute(
        """
        SELECT p.id, p.content, p.created_at, p.updated_at, p.author_id, u.username, u.profile_pic
        FROM posts p
        JOIN users u ON p.author_id = u.id
        ORDER BY p.created_at DESC
        """
    ).fetchall()

    posts = []
    for row in posts_rows:
        post_dict = dict(row)
        comments = conn.execute(
            """
            SELECT c.id, c.content, c.created_at, c.author_id, u.username, u.profile_pic
            FROM comments c
            JOIN users u ON c.author_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
            """,
            (row["id"],)
        ).fetchall()
        post_dict["comments"] = comments
        posts.append(post_dict)

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
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            flash("Conta criada com sucesso! Faça login para continuar.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Nome de usuário já existe. Escolha outro.", "danger")
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

        if not username or not password:
            flash("Preencha o nome de usuário e a senha.", "danger")
            return render_template("login.html")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Bem-vindo(a), {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Credenciais inválidas. Verifique os dados e tente novamente.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        if "profile_pic" not in request.files:
            flash("Nenhum arquivo de imagem foi enviado.", "danger")
            conn.close()
            return redirect(url_for("profile"))

        file = request.files["profile_pic"]
        if file.filename == "":
            flash("Nenhum arquivo foi selecionado.", "danger")
            conn.close()
            return redirect(url_for("profile"))

        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            unique_filename = f"user_{session['user_id']}_{uuid.uuid4().hex[:10]}.{ext}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
            file.save(file_path)

            # Exclui imagem anterior caso exista para não acumular arquivos órfãos
            if user["profile_pic"]:
                old_file_path = os.path.join(app.config["UPLOAD_FOLDER"], user["profile_pic"])
                if os.path.exists(old_file_path):
                    try:
                        os.remove(old_file_path)
                    except OSError:
                        pass

            conn.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (unique_filename, session["user_id"]))
            conn.commit()
            conn.close()

            flash("Foto de perfil atualizada com sucesso!", "success")
            return redirect(url_for("profile"))
        else:
            flash("Formato de imagem inválido. Formatos suportados: PNG, JPG, JPEG, GIF, WEBP.", "danger")
            conn.close()
            return redirect(url_for("profile"))

    conn.close()
    return render_template("profile.html", user=user)

@app.route("/posts/create", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content", "").strip()

    if not content:
        flash("A publicação não pode estar vazia.", "danger")
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute("INSERT INTO posts (author_id, content) VALUES (?, ?)", (session["user_id"], content))
    conn.commit()
    conn.close()

    flash("Postagem publicada com sucesso!", "success")
    return redirect(url_for("index"))

@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = get_post(post_id, check_author=True)

    if request.method == "POST":
        content = request.form.get("content", "").strip()

        if not content:
            flash("O conteúdo da postagem não pode ser vazio.", "danger")
            return render_template("edit_post.html", post=post)

        conn = get_db()
        conn.execute(
            """
            UPDATE posts 
            SET content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (content, post_id)
        )
        conn.commit()
        conn.close()

        flash("Postagem atualizada com sucesso!", "success")
        return redirect(url_for("index"))

    return render_template("edit_post.html", post=post)

@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    get_post(post_id, check_author=True)

    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

    flash("Postagem excluída com sucesso!", "info")
    return redirect(url_for("index"))

@app.route("/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def add_comment(post_id):
    get_post(post_id, check_author=False)

    content = request.form.get("content", "").strip()
    if not content:
        flash("O comentário não pode estar vazio.", "danger")
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        "INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)",
        (post_id, session["user_id"], content)
    )
    conn.commit()
    conn.close()

    flash("Comentário adicionado com sucesso!", "success")
    return redirect(url_for("index"))

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    users = []
    posts = []

    if query:
        search_pattern = f"%{query}%"
        conn = get_db()

        users = conn.execute(
            """
            SELECT id, username, profile_pic, created_at
            FROM users
            WHERE username LIKE ?
            ORDER BY username ASC
            """,
            (search_pattern,)
        ).fetchall()

        posts_rows = conn.execute(
            """
            SELECT p.id, p.content, p.created_at, p.updated_at, p.author_id, u.username, u.profile_pic
            FROM posts p
            JOIN users u ON p.author_id = u.id
            WHERE p.content LIKE ?
            ORDER BY p.created_at DESC
            """,
            (search_pattern,)
        ).fetchall()

        for row in posts_rows:
            post_dict = dict(row)
            comments = conn.execute(
                """
                SELECT c.id, c.content, c.created_at, c.author_id, u.username, u.profile_pic
                FROM comments c
                JOIN users u ON c.author_id = u.id
                WHERE c.post_id = ?
                ORDER BY c.created_at ASC
                """,
                (row["id"],)
            ).fetchall()
            post_dict["comments"] = comments
            posts.append(post_dict)

        conn.close()

    return render_template("search.html", query=query, users=users, posts=posts)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
