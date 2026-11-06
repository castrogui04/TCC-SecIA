from collections import defaultdict

from flask import Blueprint, abort, flash, g, redirect, request, url_for

from .auth import login_required
from .db import get_db

bp = Blueprint("comentarios", __name__, url_prefix="/posts")

COMENTARIO_MAX = 500


def comentarios_por_postagem(ids_postagens):
    """Retorna {postagem_id: [comentários]} para as postagens informadas.

    Busca tudo em uma única consulta, em ordem cronológica, já com o nome
    do autor de cada comentário.
    """
    agrupados = defaultdict(list)
    if not ids_postagens:
        return agrupados

    marcadores = ",".join("?" for _ in ids_postagens)
    linhas = get_db().execute(
        f"""
        SELECT c.id, c.postagem_id, c.conteudo, c.criado_em,
               c.autor_id, u.username AS autor
          FROM comentarios c
          JOIN usuarios u ON u.id = c.autor_id
         WHERE c.postagem_id IN ({marcadores})
         ORDER BY c.criado_em ASC, c.id ASC
        """,
        tuple(ids_postagens),
    ).fetchall()

    for linha in linhas:
        agrupados[linha["postagem_id"]].append(linha)
    return agrupados


@bp.route("/<int:post_id>/comentarios", methods=("POST",))
@login_required
def adicionar(post_id):
    db = get_db()

    postagem = db.execute(
        "SELECT id FROM postagens WHERE id = ?", (post_id,)
    ).fetchone()
    if postagem is None:
        abort(404, description="Postagem não encontrada.")

    conteudo = request.form.get("conteudo", "").strip()
    destino = url_for("main.index", _anchor=f"post-{post_id}")

    if not conteudo:
        flash("O comentário não pode ficar vazio.", "erro")
        return redirect(destino)
    if len(conteudo) > COMENTARIO_MAX:
        flash(f"O comentário pode ter no máximo {COMENTARIO_MAX} caracteres.", "erro")
        return redirect(destino)

    db.execute(
        "INSERT INTO comentarios (postagem_id, autor_id, conteudo) VALUES (?, ?, ?)",
        (post_id, g.user["id"], conteudo),
    )
    db.commit()
    flash("Comentário adicionado.", "sucesso")
    return redirect(destino)
