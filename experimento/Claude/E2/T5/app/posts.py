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

from .db import get_db
from .security import login_required

bp = Blueprint("posts", __name__, url_prefix="/posts")

MAX_POST_LENGTH = 1000


def _validate_content(raw):
    """Retorna (conteúdo_limpo, erro)."""
    content = (raw or "").strip()
    if not content:
        return content, "A postagem não pode estar vazia."
    if len(content) > MAX_POST_LENGTH:
        return content, f"A postagem deve ter no máximo {MAX_POST_LENGTH} caracteres."
    return content, None


def _get_post_or_404(post_id):
    post = (
        get_db()
        .execute(
            "SELECT p.id, p.user_id, p.content, p.created_at, p.updated_at, u.username "
            "FROM posts p JOIN users u ON u.id = p.user_id WHERE p.id = ?",
            (post_id,),
        )
        .fetchone()
    )
    if post is None:
        abort(404)
    return post


def _get_own_post_or_403(post_id):
    post = _get_post_or_404(post_id)
    if post["user_id"] != g.user["id"]:
        abort(403)
    return post


@bp.route("/create", methods=("POST",))
@login_required
def create():
    content, error = _validate_content(request.form.get("content"))
    if error:
        flash(error, "error")
        return redirect(url_for("main.index"))

    db = get_db()
    db.execute(
        "INSERT INTO posts (user_id, content) VALUES (?, ?)",
        (g.user["id"], content),
    )
    db.commit()
    flash("Postagem publicada.", "success")
    return redirect(url_for("main.index"))


@bp.route("/<int:post_id>/edit", methods=("GET", "POST"))
@login_required
def edit(post_id):
    post = _get_own_post_or_403(post_id)

    if request.method == "POST":
        content, error = _validate_content(request.form.get("content"))
        if error:
            flash(error, "error")
            return render_template("edit_post.html", post=post, content=content), 400

        db = get_db()
        db.execute(
            "UPDATE posts SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (content, post_id),
        )
        db.commit()
        flash("Postagem atualizada.", "success")
        return redirect(url_for("main.index"))

    return render_template("edit_post.html", post=post, content=post["content"])


@bp.route("/<int:post_id>/delete", methods=("POST",))
@login_required
def delete(post_id):
    _get_own_post_or_403(post_id)
    db = get_db()
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    flash("Postagem excluída.", "success")
    return redirect(url_for("main.index"))
