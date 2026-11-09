import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializa o banco de dados e cria tabelas se não existirem
with app.app_context():
    init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Você precisa estar autenticado para acessar esta página.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    user = None
    conn = get_db_connection()
    
    if "user_id" in session:
        user = conn.execute(
            "SELECT id, username FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()

    # Busca todas as postagens unindo com a tabela de usuários para obter o autor
    posts = conn.execute("""
        SELECT p.id, p.content, p.created_at, p.user_id, u.username
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC, p.id DESC
    """).fetchall()
    
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

    # Garante que apenas o criador pode editar a postagem
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

    # Garante que apenas o criador pode excluir a postagem
    if post["user_id"] != session["user_id"]:
        conn.close()
        flash("Você não tem permissão para excluir esta postagem.", "danger")
        return redirect(url_for("index"))

    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

    flash("Postagem excluída com sucesso!", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
