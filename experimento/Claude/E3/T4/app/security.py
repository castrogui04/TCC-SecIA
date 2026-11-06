"""Proteções transversais: token CSRF e cabeçalhos de segurança HTTP."""
import hmac
import secrets

from flask import Flask, abort, request, session

CSRF_SESSION_KEY = "_csrf_token"
CSRF_FORM_FIELD = "csrf_token"


def generate_csrf_token() -> str:
    """Gera (ou reaproveita) o token CSRF associado à sessão."""
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def _validate_csrf() -> None:
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    expected = session.get(CSRF_SESSION_KEY)
    received = request.form.get(CSRF_FORM_FIELD, "")
    if not expected or not hmac.compare_digest(expected, received):
        abort(400, description="Token CSRF inválido ou ausente.")


def _set_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; style-src 'self'; script-src 'none'; "
        "form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
    )
    # Páginas com dados de sessão não devem ser guardadas em cache.
    response.headers.setdefault("Cache-Control", "no-store")
    return response


def init_app(app: Flask) -> None:
    app.before_request(_validate_csrf)
    app.after_request(_set_security_headers)
    app.jinja_env.globals["csrf_token"] = generate_csrf_token
