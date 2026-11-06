"""Proteção simples contra CSRF, sem dependências externas.

Cada sessão recebe um token aleatório. Todo formulário POST precisa enviar
esse token no campo oculto "csrf_token"; caso contrário a requisição é
recusada com erro 400.
"""
import hmac
import secrets

from flask import abort, request, session

CAMPO = "csrf_token"


def gerar_token():
    token = session.get(CAMPO)
    if token is None:
        token = secrets.token_hex(32)
        session[CAMPO] = token
    return token


def validar_token():
    if request.method != "POST":
        return
    esperado = session.get(CAMPO)
    recebido = request.form.get(CAMPO, "")
    if not esperado or not hmac.compare_digest(esperado, recebido):
        abort(400, description="Token CSRF ausente ou inválido. Recarregue a página e tente novamente.")


def init_app(app):
    app.before_request(validar_token)
    # Disponibiliza csrf_token() em todos os templates.
    app.jinja_env.globals["csrf_token"] = gerar_token
