"""Cadastro, login, logout e controle de sessão de usuários."""
import functools
import re
import sqlite3
from urllib.parse import urlparse

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 128

# Hash "falso" usado quando o usuário não existe, para que o tempo de
# resposta do login não revele quais nomes de usuário estão cadastrados.
_DUMMY_HASH = generate_password_hash("senha-inexistente-para-tempo-constante")


def login_required(view):
    """Decorator que exige usuário autenticado."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Faça login para acessar esta página.", "info")
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user() -> None:
    """Carrega o usuário autenticado (se houver) a partir da sessão."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return

    g.user = get_db().execute(
        "SELECT id, username, created_at, avatar_filename FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    # Usuário removido do banco: descarta a sessão órfã.
    if g.user is None:
        session.clear()


def _is_safe_redirect(target: str | None) -> bool:
    """Aceita apenas caminhos relativos do próprio site (evita open redirect)."""
    if not target:
        return False
    parsed = urlparse(target)
    return (
        not parsed.scheme
        and not parsed.netloc
        and target.startswith("/")
        and not target.startswith("//")
        and "\\" not in target
    )


def _validate_registration(username: str, password: str, confirm: str) -> str | None:
    if not username:
        return "Informe um nome de usuário."
    if not USERNAME_RE.fullmatch(username):
        return (
            "O nome de usuário deve ter de 3 a 30 caracteres e conter apenas "
            "letras, números, ponto, hífen ou sublinhado."
        )
    if not password:
        return "Informe uma senha."
    if len(password) < PASSWORD_MIN_LEN:
        return f"A senha deve ter pelo menos {PASSWORD_MIN_LEN} caracteres."
    if len(password) > PASSWORD_MAX_LEN:
        return f"A senha deve ter no máximo {PASSWORD_MAX_LEN} caracteres."
    if password != confirm:
        return "As senhas não coincidem."
    return None


def _start_session(user_id: int) -> None:
    # Limpa a sessão anterior para evitar fixação de sessão
    # e gera um novo token CSRF para a sessão autenticada.
    session.clear()
    session["user_id"] = user_id
    session.permanent = True


@bp.route("/register", methods=("GET", "POST"))
def register():
    if g.user is not None:
        return redirect(url_for("main.index"))

    username = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = _validate_registration(username, password, confirm)

        if error is None:
            conn = get_db()
            try:
                cursor = conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                error = "Este nome de usuário já está em uso."
            else:
                _start_session(cursor.lastrowid)
                flash("Cadastro realizado com sucesso. Bem-vindo(a)!", "success")
                return redirect(url_for("main.index"))

        flash(error, "error")

    return render_template("auth/register.html", username=username)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(url_for("main.index"))

    username = ""
    next_url = request.values.get("next", "")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = None
        if username and password and len(password) <= PASSWORD_MAX_LEN:
            user = get_db().execute(
                "SELECT id, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if user is not None:
            valid = check_password_hash(user["password_hash"], password)
        else:
            check_password_hash(_DUMMY_HASH, password[:PASSWORD_MAX_LEN])
            valid = False

        if valid:
            _start_session(user["id"])
            flash("Login realizado com sucesso.", "success")
            if _is_safe_redirect(next_url):
                return redirect(next_url)
            return redirect(url_for("main.index"))

        # Mensagem genérica: não revela se o usuário existe.
        flash("Nome de usuário ou senha inválidos.", "error")

    if not _is_safe_redirect(next_url):
        next_url = ""
    return render_template("auth/login.html", username=username, next_url=next_url)


@bp.route("/logout", methods=("POST",))
def logout():
    # Logout só por POST (com token CSRF) para não ser disparado por links.
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))
