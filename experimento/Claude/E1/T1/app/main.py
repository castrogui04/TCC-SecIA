from flask import Blueprint, render_template

from .auth import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # A página inicial mostra o usuário autenticado (g.user) ou,
    # se ninguém estiver logado, os links de login e cadastro.
    return render_template("index.html")


@bp.route("/perfil")
@login_required
def perfil():
    return render_template("perfil.html")
