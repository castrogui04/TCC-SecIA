from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import login_required
from .comentarios import COMENTARIO_MAX, comentarios_por_postagem
from .db import get_db

bp = Blueprint("busca", __name__)

TERMO_MAX = 100
LIMITE_RESULTADOS = 50


def escapar_like(termo):
    """Escapa os curingas do LIKE (% e _) para que sejam tratados como texto.

    Assim, buscar "50%" procura literalmente por "50%", e não por
    "50 seguido de qualquer coisa".
    """
    return (
        termo.replace("\\", "\\\\")
             .replace("%", "\\%")
             .replace("_", "\\_")
    )


def buscar_usuarios(termo):
    padrao = f"%{escapar_like(termo)}%"
    return get_db().execute(
        """
        SELECT u.id, u.username, u.criado_em,
               (SELECT COUNT(*) FROM postagens p WHERE p.autor_id = u.id) AS total_postagens
          FROM usuarios u
         WHERE u.username LIKE ? ESCAPE '\\'
         ORDER BY
               CASE WHEN u.username = ? COLLATE NOCASE THEN 0 ELSE 1 END,
               u.username COLLATE NOCASE
         LIMIT ?
        """,
        (padrao, termo, LIMITE_RESULTADOS),
    ).fetchall()


def buscar_postagens(termo):
    padrao = f"%{escapar_like(termo)}%"
    return get_db().execute(
        """
        SELECT p.id, p.conteudo, p.criado_em, p.atualizado_em,
               p.autor_id, u.username AS autor
          FROM postagens p
          JOIN usuarios u ON u.id = p.autor_id
         WHERE p.conteudo LIKE ? ESCAPE '\\'
         ORDER BY p.criado_em DESC, p.id DESC
         LIMIT ?
        """,
        (padrao, LIMITE_RESULTADOS),
    ).fetchall()


@bp.route("/busca")
@login_required
def buscar():
    termo = request.args.get("q", "").strip()

    if len(termo) > TERMO_MAX:
        flash(f"O termo de busca pode ter no máximo {TERMO_MAX} caracteres.", "erro")
        return redirect(url_for("main.index"))

    usuarios = []
    postagens = []
    if termo:
        usuarios = buscar_usuarios(termo)
        postagens = buscar_postagens(termo)

    comentarios = comentarios_por_postagem([p["id"] for p in postagens])

    return render_template(
        "busca.html",
        termo_busca=termo,
        usuarios=usuarios,
        postagens=postagens,
        comentarios=comentarios,
        comentario_max=COMENTARIO_MAX,
        limite=LIMITE_RESULTADOS,
    )
