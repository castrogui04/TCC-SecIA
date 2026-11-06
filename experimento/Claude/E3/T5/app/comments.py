"""Comentários nas postagens."""
from collections import defaultdict

from flask import Blueprint, abort, flash, g, redirect, request, url_for

from .auth import login_required
from .db import get_db

bp = Blueprint("comments", __name__, url_prefix="/posts")

COMMENT_MAX_LEN = 300


def comments_by_post() -> dict[int, list]:
    """Todos os comentários, agrupados por post_id (mais antigos primeiro)."""
    rows = get_db().execute(
        "SELECT c.id, c.post_id, c.user_id, c.content, c.created_at, "
        "       u.username AS author, u.avatar_filename AS author_avatar "
        "FROM comments c JOIN users u ON u.id = c.user_id "
        "ORDER BY c.created_at ASC, c.id ASC"
    ).fetchall()
    grouped: dict[int, list] = defaultdict(list)
    for row in rows:
        grouped[row["post_id"]].append(row)
    return grouped


def _validate_content(raw: str) -> tuple[str, str | None]:
    content = raw.replace("\r\n", "\n").strip()
    if not content:
        return content, "O comentário não pode estar vazio."
    if len(content) > COMMENT_MAX_LEN:
        return content, f"O comentário deve ter no máximo {COMMENT_MAX_LEN} caracteres."
    return content, None


@bp.route("/<int:post_id>/comments", methods=("POST",))
@login_required
def create(post_id: int):
    conn = get_db()
    if conn.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)).fetchone() is None:
        abort(404)

    content, error = _validate_content(request.form.get("content", ""))
    if error:
        flash(error, "error")
    else:
        conn.execute(
            "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
            (post_id, g.user["id"], content),
        )
        conn.commit()
        flash("Comentário adicionado.", "success")
    return redirect(url_for("main.index", _anchor=f"post-{post_id}"))
