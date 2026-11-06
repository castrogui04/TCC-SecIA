"""Páginas principais da aplicação."""
from flask import Blueprint, render_template

from .posts import list_posts

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # O template usa g.user para mostrar quem está autenticado.
    return render_template("index.html", posts=list_posts(), draft="")
