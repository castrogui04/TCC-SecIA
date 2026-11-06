from flask import Blueprint, g, render_template

from .auth import login_required
from .db import get_db
from .posts import CONTEUDO_MAX, listar_postagens

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # Usuário autenticado: vê quem está logado, o formulário de nova
    # postagem e o feed. Visitante: vê os links de login e cadastro.
    postagens = listar_postagens() if g.user else []
    return render_template(
        "index.html", postagens=postagens, conteudo_max=CONTEUDO_MAX
    )


@bp.route("/perfil")
@login_required
def perfil():
    total = get_db().execute(
        "SELECT COUNT(*) FROM postagens WHERE autor_id = ?", (g.user["id"],)
    ).fetchone()[0]
    return render_template("perfil.html", total_postagens=total)
