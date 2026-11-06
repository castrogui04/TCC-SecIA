from flask import (
    Blueprint, abort, flash, g, redirect, render_template, request, url_for
)

from .auth import login_required
from .db import get_db

bp = Blueprint("posts", __name__, url_prefix="/posts")

CONTEUDO_MAX = 1000


def listar_postagens():
    """Todas as postagens, das mais recentes para as mais antigas, com o autor."""
    return get_db().execute(
        """
        SELECT p.id, p.conteudo, p.criado_em, p.atualizado_em,
               p.autor_id, u.username AS autor
          FROM postagens p
          JOIN usuarios u ON u.id = p.autor_id
         ORDER BY p.criado_em DESC, p.id DESC
        """
    ).fetchall()


def obter_postagem(post_id, verificar_autor=True):
    """Busca uma postagem; 404 se não existir, 403 se não pertencer ao usuário."""
    postagem = get_db().execute(
        """
        SELECT p.id, p.conteudo, p.criado_em, p.atualizado_em,
               p.autor_id, u.username AS autor
          FROM postagens p
          JOIN usuarios u ON u.id = p.autor_id
         WHERE p.id = ?
        """,
        (post_id,),
    ).fetchone()

    if postagem is None:
        abort(404, description="Postagem não encontrada.")

    if verificar_autor and postagem["autor_id"] != g.user["id"]:
        abort(403, description="Você só pode alterar as suas próprias postagens.")

    return postagem


def validar_conteudo(conteudo):
    if not conteudo:
        return "A postagem não pode ficar vazia."
    if len(conteudo) > CONTEUDO_MAX:
        return f"A postagem pode ter no máximo {CONTEUDO_MAX} caracteres."
    return None


@bp.route("/nova", methods=("POST",))
@login_required
def nova():
    conteudo = request.form.get("conteudo", "").strip()
    erro = validar_conteudo(conteudo)

    if erro is not None:
        flash(erro, "erro")
        return redirect(url_for("main.index"))

    db = get_db()
    db.execute(
        "INSERT INTO postagens (autor_id, conteudo) VALUES (?, ?)",
        (g.user["id"], conteudo),
    )
    db.commit()
    flash("Postagem publicada!", "sucesso")
    return redirect(url_for("main.index"))


@bp.route("/<int:post_id>/editar", methods=("GET", "POST"))
@login_required
def editar(post_id):
    postagem = obter_postagem(post_id)

    if request.method == "POST":
        conteudo = request.form.get("conteudo", "").strip()
        erro = validar_conteudo(conteudo)

        if erro is not None:
            flash(erro, "erro")
            return render_template(
                "posts/editar.html", postagem=postagem, conteudo=conteudo,
                conteudo_max=CONTEUDO_MAX,
            ), 400

        db = get_db()
        db.execute(
            """
            UPDATE postagens
               SET conteudo = ?, atualizado_em = CURRENT_TIMESTAMP
             WHERE id = ? AND autor_id = ?
            """,
            (conteudo, post_id, g.user["id"]),
        )
        db.commit()
        flash("Postagem atualizada.", "sucesso")
        return redirect(url_for("main.index"))

    return render_template(
        "posts/editar.html", postagem=postagem, conteudo=postagem["conteudo"],
        conteudo_max=CONTEUDO_MAX,
    )


@bp.route("/<int:post_id>/excluir", methods=("POST",))
@login_required
def excluir(post_id):
    obter_postagem(post_id)

    db = get_db()
    db.execute(
        "DELETE FROM postagens WHERE id = ? AND autor_id = ?",
        (post_id, g.user["id"]),
    )
    db.commit()
    flash("Postagem excluída.", "sucesso")
    return redirect(url_for("main.index"))
