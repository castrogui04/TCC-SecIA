import functools
import re
import sqlite3

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
SENHA_MIN = 6


@bp.before_app_request
def carregar_usuario_logado():
    """Antes de cada requisição, carrega o usuário da sessão em g.user."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT id, username, criado_em FROM usuarios WHERE id = ?",
            (user_id,),
        ).fetchone()
        if g.user is None:
            # Usuário removido do banco: descarta a sessão antiga.
            session.clear()


def login_required(view):
    """Decorador que exige usuário autenticado para acessar a rota."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Faça login para acessar esta página.", "erro")
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view


@bp.route("/cadastro", methods=("GET", "POST"))
def cadastro():
    if g.user is not None:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")
        erro = None

        if not username:
            erro = "Informe um nome de usuário."
        elif not USERNAME_REGEX.match(username):
            erro = ("O nome de usuário deve ter de 3 a 30 caracteres "
                    "(letras, números, '.', '_' ou '-').")
        elif not senha:
            erro = "Informe uma senha."
        elif len(senha) < SENHA_MIN:
            erro = f"A senha deve ter pelo menos {SENHA_MIN} caracteres."
        elif senha != confirmacao:
            erro = "As senhas não conferem."

        if erro is None:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO usuarios (username, senha_hash) VALUES (?, ?)",
                    (username, generate_password_hash(senha)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                erro = f"O usuário '{username}' já está cadastrado."
            else:
                flash("Cadastro realizado com sucesso! Faça login.", "sucesso")
                return redirect(url_for("auth.login"))

        flash(erro, "erro")
        return render_template("auth/cadastro.html", username=username), 400

    return render_template("auth/cadastro.html", username="")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")
        lembrar = request.form.get("lembrar") == "on"

        usuario = get_db().execute(
            "SELECT id, username, senha_hash FROM usuarios WHERE username = ?",
            (username,),
        ).fetchone()

        # Mesma mensagem nos dois casos, para não revelar quais usuários existem.
        if usuario is None or not check_password_hash(usuario["senha_hash"], senha):
            flash("Usuário ou senha incorretos.", "erro")
            return render_template("auth/login.html", username=username), 401

        session.clear()  # evita fixação de sessão
        session["user_id"] = usuario["id"]
        session.permanent = lembrar  # "lembrar de mim" mantém por 7 dias
        flash(f"Bem-vindo(a), {usuario['username']}!", "sucesso")
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", username="")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("auth.login"))
