import re
import sqlite3

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
MIN_PASSWORD = 8
MAX_PASSWORD = 128

# Hash válido usado quando o usuário não existe, para que o tempo de resposta
# do login seja semelhante em ambos os casos (evita enumeração por tempo).
_DUMMY_HASH = generate_password_hash("senha-ficticia-para-timing")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = (
            get_db()
            .execute("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,))
            .fetchone()
        )
        if g.user is None:
            session.clear()


def _safe_next(target):
    """Aceita apenas caminhos relativos internos para evitar open redirect."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return url_for("main.index")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if g.user:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        error = None

        if not USERNAME_RE.fullmatch(username):
            error = "Nome de usuário deve ter 3 a 30 caracteres (letras, números, _ . -)."
        elif not (MIN_PASSWORD <= len(password) <= MAX_PASSWORD):
            error = f"A senha deve ter entre {MIN_PASSWORD} e {MAX_PASSWORD} caracteres."
        elif password != confirm:
            error = "As senhas não coincidem."

        if error is None:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                error = "Este nome de usuário já está em uso."
            else:
                flash("Cadastro realizado com sucesso. Faça login.", "success")
                return redirect(url_for("auth.login"))

        flash(error, "error")
        return render_template("register.html", username=username), 400

    return render_template("register.html", username="")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = get_db().execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        stored_hash = user["password_hash"] if user else _DUMMY_HASH
        password_ok = check_password_hash(stored_hash, password[:MAX_PASSWORD])

        if user is None or not password_ok:
            flash("Usuário ou senha inválidos.", "error")
            return render_template("login.html", username=username), 401

        next_url = _safe_next(request.args.get("next"))
        # Nova sessão a cada login (evita fixação de sessão).
        session.clear()
        session["user_id"] = user["id"]
        session.permanent = remember
        flash(f"Bem-vindo, {user['username']}!", "success")
        return redirect(next_url)

    return render_template("login.html", username="")


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "success")
    return redirect(url_for("auth.login"))
