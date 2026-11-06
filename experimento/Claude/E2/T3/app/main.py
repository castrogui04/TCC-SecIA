from collections import defaultdict

from flask import Blueprint, render_template

from .db import get_db
from .security import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    db = get_db()
    posts = db.execute(
        "SELECT p.id, p.user_id, p.content, p.created_at, p.updated_at, u.username "
        "FROM posts p JOIN users u ON u.id = p.user_id "
        "ORDER BY p.created_at DESC, p.id DESC"
    ).fetchall()

    # Uma única consulta para todos os comentários, agrupados por postagem.
    comments_by_post = defaultdict(list)
    rows = db.execute(
        "SELECT c.id, c.post_id, c.content, c.created_at, u.username "
        "FROM comments c JOIN users u ON u.id = c.user_id "
        "ORDER BY c.created_at ASC, c.id ASC"
    ).fetchall()
    for row in rows:
        comments_by_post[row["post_id"]].append(row)

    return render_template("index.html", posts=posts, comments_by_post=comments_by_post)
