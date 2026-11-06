import os
import secrets
from datetime import timedelta

from flask import Flask


def _carregar_secret_key(instance_path):
    """Lê a SECRET_KEY do ambiente ou de um arquivo na pasta instance.

    Se não existir, gera uma chave aleatória e a salva, para que as sessões
    continuem válidas mesmo depois de reiniciar o servidor.
    """
    chave_env = os.environ.get("SECRET_KEY")
    if chave_env:
        return chave_env

    caminho = os.path.join(instance_path, "secret_key")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read().strip()

    chave = secrets.token_hex(32)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(chave)
    return chave


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # A pasta instance guarda o banco SQLite e a chave secreta.
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=_carregar_secret_key(app.instance_path),
        DATABASE=os.path.join(app.instance_path, "rede_social.sqlite"),
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=64 * 1024,  # limita o tamanho das requisições
    )

    from . import db
    db.init_app(app)

    from . import csrf
    csrf.init_app(app)

    from . import auth, busca, comentarios, main, posts
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(comentarios.bp)
    app.register_blueprint(busca.bp)

    return app
