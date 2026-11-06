"""Perfil do usuário: envio, substituição e exibição da foto de perfil."""
import io
import os
import re
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
from PIL import Image, ImageOps, UnidentifiedImageError

from .auth import login_required
from .db import get_db

bp = Blueprint("profile", __name__)

ALLOWED_FORMATS = {"PNG", "JPEG", "GIF", "WEBP"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024      # 2 MB
MAX_PIXELS = 25_000_000                 # evita "decompression bombs"
AVATAR_SIZE = 256                       # lado do quadrado final, em pixels
AVATAR_NAME_RE = re.compile(r"^[0-9a-f]{32}\.png$")


class AvatarError(Exception):
    """Erro de validação mostrado ao usuário."""


def _process_image(data: bytes) -> bytes:
    """Valida a imagem e a reprocessa para um PNG quadrado de 256x256.

    O conteúdo é decodificado e gravado novamente pelo Pillow: nada do
    arquivo original (metadados EXIF, dados extras, scripts anexados) é
    preservado. A validação olha o conteúdo, nunca o nome ou o tipo MIME
    informados pelo cliente.
    """
    if not data:
        raise AvatarError("Selecione uma imagem para enviar.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise AvatarError("A imagem deve ter no máximo 2 MB.")

    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            width, height = probe.size
            if fmt not in ALLOWED_FORMATS:
                raise AvatarError("Formato não suportado. Use PNG, JPEG, GIF ou WebP.")
            if width * height > MAX_PIXELS:
                raise AvatarError("A imagem tem dimensões grandes demais.")
            probe.verify()

        # verify() invalida o objeto; abre novamente para decodificar.
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)      # respeita a orientação
            img = img.convert("RGBA")               # GIF/WebP: primeiro quadro
            img = ImageOps.fit(img, (AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
            out = io.BytesIO()
            img.save(out, format="PNG", optimize=True)
            return out.getvalue()
    except AvatarError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError,
            ValueError, SyntaxError):
        raise AvatarError("O arquivo enviado não é uma imagem válida.")


def _avatar_path(filename: str) -> str:
    return os.path.join(current_app.config["AVATAR_DIR"], filename)


def _remove_avatar_file(filename: str | None) -> None:
    if filename and AVATAR_NAME_RE.fullmatch(filename):
        try:
            os.remove(_avatar_path(filename))
        except OSError:
            pass


@bp.route("/profile")
@login_required
def show():
    return render_template("profile.html")


@bp.route("/profile/avatar", methods=("POST",))
@login_required
def upload_avatar():
    file = request.files.get("avatar")
    if file is None or not file.filename:
        flash("Selecione uma imagem para enviar.", "error")
        return render_template("profile.html"), 400

    try:
        # Lê no máximo 1 byte além do limite para detectar arquivos grandes.
        png = _process_image(file.stream.read(MAX_UPLOAD_BYTES + 1))
    except AvatarError as exc:
        flash(str(exc), "error")
        return render_template("profile.html"), 400

    new_name = f"{secrets.token_hex(16)}.png"
    tmp_path = _avatar_path(new_name + ".tmp")
    with open(tmp_path, "wb") as f:
        f.write(png)
    os.replace(tmp_path, _avatar_path(new_name))

    old_name = g.user["avatar_filename"]
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET avatar_filename = ? WHERE id = ?",
            (new_name, g.user["id"]),
        )
        conn.commit()
    except Exception:
        _remove_avatar_file(new_name)
        raise

    _remove_avatar_file(old_name)   # substitui: apaga a foto anterior
    flash("Foto de perfil atualizada.", "success")
    return redirect(url_for("profile.show"))


@bp.route("/avatars/<filename>")
def avatar_file(filename: str):
    """Serve as fotos de perfil (públicas, pois aparecem nas postagens)."""
    if not AVATAR_NAME_RE.fullmatch(filename):
        return ("Não encontrado", 404)
    response = send_from_directory(
        current_app.config["AVATAR_DIR"],
        filename,
        mimetype="image/png",
        max_age=31536000,
    )
    # O nome do arquivo muda a cada troca de foto, então o cache é seguro.
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response
