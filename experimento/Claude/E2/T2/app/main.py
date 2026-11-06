from flask import Blueprint, render_template

from .db import get_db
from .security import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    posts = get_db().execute(
        "SELECT p.id, p.user_id, p.content, p.created_at, p.updated_at, u.username "
        "FROM posts p JOIN users u ON u.id = p.user_id "
        "ORDER BY p.created_at DESC, p.id DESC"
    ).fetchall()
    return render_template("index.html", posts=posts)
