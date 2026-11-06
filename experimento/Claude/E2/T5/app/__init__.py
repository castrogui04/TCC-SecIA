import os
import secrets
from datetime import timedelta

from flask import Flask, flash, redirect, url_for

from . import db
from .auth import bp as auth_bp
from .comments import bp as comments_bp
from .main import bp as main_bp
from .profile import avatar_url, bp as profile_bp
from .posts import bp as posts_bp
from .search import bp as search_bp
from .security import init_csrf


def _load_secret_key(instance_path):
    """Usa SECRET_KEY do ambiente ou gera/persiste uma chave aleatória em instance/."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    key_file = os.path.join(instance_path, "secret_key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(key_file, "w", encoding="utf-8") as f:
        f.write(key)
    try:
        os.chmod(key_file, 0o600)
    except OSError:
        pass
    return key


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=_load_secret_key(app.instance_path),
        DATABASE=os.path.join(app.instance_path, "rede_social.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        # Limite do corpo da requisição (a foto tem limite próprio de 2 MB).
        MAX_CONTENT_LENGTH=3 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    init_csrf(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(profile_bp)
    app.jinja_env.globals["avatar_url"] = avatar_url

    @app.errorhandler(413)
    def _too_large(_error):
        flash("O arquivo enviado é grande demais (máximo 2 MB).", "error")
        return redirect(url_for("profile.profile"))

    with app.app_context():
        db.init_db()

    return app
