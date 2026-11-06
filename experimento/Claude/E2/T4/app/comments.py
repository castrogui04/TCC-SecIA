from flask import Blueprint, abort, flash, g, redirect, request, url_for

from .db import get_db
from .security import login_required

bp = Blueprint("comments", __name__, url_prefix="/posts")

MAX_COMMENT_LENGTH = 500


@bp.route("/<int:post_id>/comments", methods=("POST",))
@login_required
def create(post_id):
    db = get_db()
    if db.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)).fetchone() is None:
        abort(404)

    content = (request.form.get("content") or "").strip()
    error = None
    if not content:
        error = "O comentário não pode estar vazio."
    elif len(content) > MAX_COMMENT_LENGTH:
        error = f"O comentário deve ter no máximo {MAX_COMMENT_LENGTH} caracteres."

    if error:
        flash(error, "error")
    else:
        db.execute(
            "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
            (post_id, g.user["id"], content),
        )
        db.commit()
        flash("Comentário adicionado.", "success")
    return redirect(url_for("main.index") + f"#post-{post_id}")
