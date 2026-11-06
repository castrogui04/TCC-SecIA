from flask import Blueprint, g, render_template

from .auth import login_required
from .avatar import TAMANHO_MAX_MB, tem_avatar
from .comentarios import COMENTARIO_MAX, comentarios_por_postagem
from .db import get_db
from .posts import CONTEUDO_MAX, listar_postagens

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # Usuário autenticado: vê quem está logado, o formulário de nova
    # postagem e o feed com os comentários. Visitante: vê os links de
    # login e cadastro.
    postagens = listar_postagens() if g.user else []
    comentarios = comentarios_por_postagem([p["id"] for p in postagens])
    return render_template(
        "index.html",
        postagens=postagens,
        comentarios=comentarios,
        conteudo_max=CONTEUDO_MAX,
        comentario_max=COMENTARIO_MAX,
    )


@bp.route("/perfil")
@login_required
def perfil():
    db = get_db()
    total_postagens = db.execute(
        "SELECT COUNT(*) FROM postagens WHERE autor_id = ?", (g.user["id"],)
    ).fetchone()[0]
    total_comentarios = db.execute(
        "SELECT COUNT(*) FROM comentarios WHERE autor_id = ?", (g.user["id"],)
    ).fetchone()[0]
    return render_template(
        "perfil.html",
        total_postagens=total_postagens,
        total_comentarios=total_comentarios,
        tem_avatar=tem_avatar(g.user["id"]),
        tamanho_max_mb=TAMANHO_MAX_MB,
    )
