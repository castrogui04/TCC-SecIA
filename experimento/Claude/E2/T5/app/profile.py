import os
import secrets

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from .db import get_db
from .security import login_required

bp = Blueprint("profile", __name__)

MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 MB


def detect_image_type(data):
    """Identifica o formato pelos bytes iniciais (não confia no nome nem no
    Content-Type enviados pelo navegador). Retorna a extensão ou None."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def avatar_url(filename):
    """URL da foto de perfil; usa a imagem padrão se o usuário não enviou uma."""
    if filename:
        return url_for("profile.avatar_file", filename=filename)
    return url_for("static", filename="default-avatar.svg")


@bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@bp.route("/profile/avatar", methods=("POST",))
@login_required
def upload_avatar():
    file = request.files.get("avatar")
    if file is None or not file.filename:
        flash("Selecione uma imagem para enviar.", "error")
        return redirect(url_for("profile.profile"))

    data = file.read(MAX_AVATAR_BYTES + 1)
    if len(data) > MAX_AVATAR_BYTES:
        flash("A imagem deve ter no máximo 2 MB.", "error")
        return redirect(url_for("profile.profile"))

    ext = detect_image_type(data)
    if ext is None:
        flash("Arquivo inválido. Envie uma imagem PNG, JPEG, GIF ou WebP.", "error")
        return redirect(url_for("profile.profile"))

    # Nome aleatório gerado pelo servidor: o nome enviado pelo usuário nunca é usado.
    filename = f"{secrets.token_hex(16)}.{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    with open(os.path.join(upload_dir, filename), "wb") as f:
        f.write(data)

    db = get_db()
    old = g.user["avatar_filename"]
    db.execute("UPDATE users SET avatar_filename = ? WHERE id = ?", (filename, g.user["id"]))
    db.commit()

    # Substituição: remove o arquivo da foto anterior.
    if old:
        try:
            os.remove(os.path.join(upload_dir, old))
        except OSError:
            pass

    flash("Foto de perfil atualizada.", "success")
    return redirect(url_for("profile.profile"))


@bp.route("/avatars/<path:filename>")
@login_required
def avatar_file(filename):
    # send_from_directory impede path traversal; nomes são aleatórios e únicos,
    # então o cache longo é seguro (uma nova foto tem uma nova URL).
    resp = send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
    resp.headers["Cache-Control"] = "private, max-age=86400"
    return resp
