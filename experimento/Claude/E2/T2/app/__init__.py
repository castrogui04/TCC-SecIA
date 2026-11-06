import os
import secrets
from datetime import timedelta

from flask import Flask

from . import db
from .auth import bp as auth_bp
from .main import bp as main_bp
from .posts import bp as posts_bp
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
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    init_csrf(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(posts_bp)

    with app.app_context():
        db.init_db()

    return app
