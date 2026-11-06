import sqlite3

import click
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    senha_hash TEXT    NOT NULL,
    criado_em  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS postagens (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    autor_id      INTEGER NOT NULL,
    conteudo      TEXT    NOT NULL,
    criado_em     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP,
    FOREIGN KEY (autor_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comentarios (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    postagem_id  INTEGER NOT NULL,
    autor_id     INTEGER NOT NULL,
    conteudo     TEXT    NOT NULL,
    criado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (postagem_id) REFERENCES postagens (id) ON DELETE CASCADE,
    FOREIGN KEY (autor_id)    REFERENCES usuarios (id)  ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_postagens_autor ON postagens (autor_id);
CREATE INDEX IF NOT EXISTS idx_postagens_criado_em ON postagens (criado_em);
CREATE INDEX IF NOT EXISTS idx_comentarios_postagem ON comentarios (postagem_id);
CREATE INDEX IF NOT EXISTS idx_comentarios_autor ON comentarios (autor_id);
"""


def get_db():
    """Retorna a conexão com o SQLite da requisição atual (uma por requisição)."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        # O SQLite só respeita chaves estrangeiras com este PRAGMA ativo.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Cria as tabelas, caso ainda não existam."""
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


@click.command("init-db")
def init_db_command():
    """Comando de terminal: flask --app run init-db"""
    init_db()
    click.echo("Banco de dados inicializado.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    # Garante que o banco e as tabelas existam já na primeira execução
    # (inclusive ao atualizar um banco criado pela versão anterior).
    with app.app_context():
        init_db()
