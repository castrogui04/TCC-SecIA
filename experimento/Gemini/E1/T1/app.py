import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)
# Chave secreta necessária para assinar os cookies de sessão com segurança
app.secret_key = os.urandom(24)

# Garante que as tabelas existam ao iniciar
with app.app_context():
    init_db()

@app.route("/")
def index():
    user = None
    if "user_id" in session:
        conn = get_db_connection()
        user = conn.execute(
            "SELECT id, username FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()
        conn.close()
    return render_template("index.html", user=user)

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

if __name__ == "__main__":
    app.run(debug=True)
