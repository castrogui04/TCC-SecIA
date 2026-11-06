"""Acesso ao banco de dados SQLite."""
import sqlite3

import click
from flask import Flask, current_app, g


def get_db() -> sqlite3.Connection:
    """Retorna a conexão SQLite da requisição atual (uma por requisição)."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # Função usada pela busca para ignorar maiúsculas/minúsculas também
        # em caracteres acentuados (o LIKE do SQLite só trata ASCII).
        g.db.create_function(
            "casefold", 1, lambda s: s.casefold() if s is not None else None,
            deterministic=True,
        )
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    """Cria as tabelas a partir de schema.sql (idempotente)."""
    conn = get_db()
    with current_app.open_resource("schema.sql") as f:
        conn.executescript(f.read().decode("utf-8"))
    conn.commit()


@click.command("init-db")
def init_db_command() -> None:
    """Comando de linha: flask --app run init-db"""
    init_db()
    click.echo("Banco de dados inicializado.")


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    # Garante que as tabelas existam ao iniciar a aplicação.
    with app.app_context():
        init_db()
