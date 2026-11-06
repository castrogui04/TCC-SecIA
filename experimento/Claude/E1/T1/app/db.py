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
"""


def get_db():
    """Retorna a conexão com o SQLite da requisição atual (uma por requisição)."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
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

    # Garante que o banco exista já na primeira execução.
    with app.app_context():
        init_db()
