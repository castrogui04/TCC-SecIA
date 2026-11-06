"""Postagens: criar, listar, editar e excluir."""
from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from .auth import login_required
from .comments import comments_by_post
from .db import get_db

bp = Blueprint("posts", __name__, url_prefix="/posts")

POST_MAX_LEN = 500


def list_posts():
    """Todas as postagens, da mais recente para a mais antiga, com o autor."""
    return get_db().execute(
        "SELECT p.id, p.content, p.created_at, p.updated_at, p.user_id, "
        "       u.username AS author "
        "FROM posts p JOIN users u ON u.id = p.user_id "
        "ORDER BY p.created_at DESC, p.id DESC"
    ).fetchall()


def get_own_post(post_id: int):
    """Retorna a postagem se ela existir e pertencer ao usuário autenticado.

    404 se não existir; 403 se pertencer a outro usuário.
    """
    post = get_db().execute(
        "SELECT p.id, p.content, p.user_id, p.created_at, u.username AS author "
        "FROM posts p JOIN users u ON u.id = p.user_id WHERE p.id = ?",
        (post_id,),
    ).fetchone()
    if post is None:
        abort(404)
    if post["user_id"] != g.user["id"]:
        abort(403)
    return post


def _validate_content(raw: str) -> tuple[str, str | None]:
    content = raw.replace("\r\n", "\n").strip()
    if not content:
        return content, "A postagem não pode estar vazia."
    if len(content) > POST_MAX_LEN:
        return content, f"A postagem deve ter no máximo {POST_MAX_LEN} caracteres."
    return content, None


@bp.route("/create", methods=("POST",))
@login_required
def create():
    content, error = _validate_content(request.form.get("content", ""))
    if error:
        flash(error, "error")
        return render_template(
            "index.html",
            posts=list_posts(),
            comments_by_post=comments_by_post(),
            draft=content,
        ), 400
    conn = get_db()
    conn.execute(
        "INSERT INTO posts (user_id, content) VALUES (?, ?)", (g.user["id"], content)
    )
    conn.commit()
    flash("Postagem publicada.", "success")
    return redirect(url_for("main.index"))


@bp.route("/<int:post_id>/edit", methods=("GET", "POST"))
@login_required
def edit(post_id: int):
    post = get_own_post(post_id)
    content = post["content"]

    if request.method == "POST":
        content, error = _validate_content(request.form.get("content", ""))
        if error:
            flash(error, "error")
            return render_template("posts/edit.html", post=post, content=content), 400
        conn = get_db()
        conn.execute(
            "UPDATE posts SET content = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND user_id = ?",
            (content, post_id, g.user["id"]),
        )
        conn.commit()
        flash("Postagem atualizada.", "success")
        return redirect(url_for("main.index"))

    return render_template("posts/edit.html", post=post, content=content)


@bp.route("/<int:post_id>/delete", methods=("GET", "POST"))
@login_required
def delete(post_id: int):
    post = get_own_post(post_id)

    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "DELETE FROM posts WHERE id = ? AND user_id = ?", (post_id, g.user["id"])
        )
        conn.commit()
        flash("Postagem excluída.", "info")
        return redirect(url_for("main.index"))

    # GET: página de confirmação (a exclusão em si exige POST + CSRF).
    return render_template("posts/delete.html", post=post)
