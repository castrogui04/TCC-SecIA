"""App Flask minimo, PROPOSITALMENTE inseguro.

Usado apenas para validar que Semgrep e Bandit detectam problemas.
NAO USE EM PRODUCAO.
"""

import sqlite3
import subprocess

from flask import Flask, request

app = Flask(__name__)
DB = "usuarios.db"


def conectar():
    return sqlite3.connect(DB)


@app.route("/usuario")
def buscar_usuario():
    # VULNERAVEL: SQL montado por concatenacao de string (SQL injection)
    nome = request.args.get("nome", "")
    conn = conectar()
    cur = conn.cursor()
    query = "SELECT id, nome, email FROM usuarios WHERE nome = '" + nome + "'"
    cur.execute(query)
    linhas = cur.fetchall()
    conn.close()
    return {"resultados": linhas}


@app.route("/ping")
def ping():
    # VULNERAVEL: entrada do usuario em comando de shell
    host = request.args.get("host", "127.0.0.1")
    saida = subprocess.check_output("ping -c 1 " + host, shell=True)
    return saida


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
