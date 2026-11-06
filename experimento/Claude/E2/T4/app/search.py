from flask import Blueprint, render_template, request

from .db import get_db
from .security import login_required

bp = Blueprint("search", __name__)

MAX_QUERY_LENGTH = 100
MAX_RESULTS = 50


def _like_pattern(term):
    """Padrão LIKE 'contém o termo', escapando %, _ e a própria barra."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


@bp.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()[:MAX_QUERY_LENGTH]
    users, posts = [], []

    if query:
        db = get_db()
        # Usuários: o nome de usuário contém o termo (sem diferenciar maiúsculas).
        users = db.execute(
            "SELECT id, username, created_at FROM users "
            "WHERE username LIKE ? ESCAPE '\\' "
            "ORDER BY username COLLATE NOCASE LIMIT ?",
            (_like_pattern(query), MAX_RESULTS),
        ).fetchall()

        # Postagens: o conteúdo contém o termo. py_lower (casefold) torna a
        # comparação insensível a maiúsculas também para letras acentuadas.
        posts = db.execute(
            "SELECT p.id, p.user_id, p.content, p.created_at, p.updated_at, u.username, "
            "       (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count "
            "FROM posts p JOIN users u ON u.id = p.user_id "
            "WHERE py_lower(p.content) LIKE ? ESCAPE '\\' "
            "ORDER BY p.created_at DESC, p.id DESC LIMIT ?",
            (_like_pattern(query.casefold()), MAX_RESULTS),
        ).fetchall()

    return render_template(
        "search.html", query=query, users=users, posts=posts, max_results=MAX_RESULTS
    )
