"""Busca de usuários (por nome) e postagens (por conteúdo)."""
from flask import Blueprint, render_template, request

from .comments import comments_by_post
from .db import get_db

bp = Blueprint("search", __name__)

QUERY_MAX_LEN = 100
RESULTS_LIMIT = 50


def _like_pattern(term: str) -> str:
    """Padrão LIKE 'contém o termo', com %, _ e \\ do usuário escapados."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped.casefold()}%"


def search_users(term: str):
    return get_db().execute(
        "SELECT u.id, u.username, u.created_at, u.avatar_filename, "
        "       (SELECT COUNT(*) FROM posts p WHERE p.user_id = u.id) AS post_count "
        "FROM users u "
        "WHERE casefold(u.username) LIKE ? ESCAPE '\\' "
        "ORDER BY u.username COLLATE NOCASE LIMIT ?",
        (_like_pattern(term), RESULTS_LIMIT),
    ).fetchall()


def search_posts(term: str):
    return get_db().execute(
        "SELECT p.id, p.content, p.created_at, p.updated_at, p.user_id, "
        "       u.username AS author, u.avatar_filename AS author_avatar "
        "FROM posts p JOIN users u ON u.id = p.user_id "
        "WHERE casefold(p.content) LIKE ? ESCAPE '\\' "
        "ORDER BY p.created_at DESC, p.id DESC LIMIT ?",
        (_like_pattern(term), RESULTS_LIMIT),
    ).fetchall()


@bp.route("/search")
def search():
    query = request.args.get("q", "").strip()[:QUERY_MAX_LEN]

    users, posts = [], []
    if query:
        users = search_users(query)
        posts = search_posts(query)

    return render_template(
        "search.html",
        query=query,
        users=users,
        posts=posts,
        comments_by_post=comments_by_post(),
        limit=RESULTS_LIMIT,
    )
