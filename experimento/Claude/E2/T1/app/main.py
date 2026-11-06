from flask import Blueprint, render_template

from .security import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def index():
    return render_template("index.html")
