"""Fábrica da aplicação Flask da rede social simplificada."""
import os
import secrets
from datetime import timedelta

from flask import Flask

from . import auth, db, main, posts, security


def _load_secret_key(instance_path: str) -> str:
    """Obtém a SECRET_KEY do ambiente ou de um arquivo persistente.

    Se não houver chave definida, gera uma chave aleatória forte e a salva
    em instance/secret_key (com permissão restrita), para que as sessões
    continuem válidas entre reinicializações.
    """
    env_key = os.environ.get("FLASK_SECRET_KEY")
    if env_key:
        return env_key

    key_path = os.path.join(instance_path, "secret_key")
    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as f:
            key = f.read().strip()
            if key:
                return key

    key = secrets.token_hex(32)
    fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(key)
    return key


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=_load_secret_key(app.instance_path),
        DATABASE=os.path.join(app.instance_path, "rede_social.sqlite3"),
        # Cookie de sessão protegido
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        # Limite de tamanho das requisições (formulários simples)
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    security.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(posts.bp)

    return app
