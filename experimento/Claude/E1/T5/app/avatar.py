"""Foto de perfil: envio, armazenamento e exibição.

A imagem enviada nunca é salva como veio do navegador. Ela é decodificada
pelo Pillow, convertida para RGB, redimensionada e regravada como JPEG.
Isso garante que o arquivo salvo é de fato uma imagem (não um arquivo
disfarçado com extensão de imagem) e descarta metadados (EXIF, comentários,
etc.) que o arquivo original pudesse conter.

Cada usuário tem no máximo um arquivo de avatar, nomeado pelo próprio ID
(ex.: instance/avatars/7.jpg), então enviar uma nova foto substitui a
anterior automaticamente.
"""
import os

from flask import (
    Blueprint, Response, abort, current_app, flash, g, redirect,
    request, send_file, url_for
)
from PIL import Image, ImageOps, UnidentifiedImageError

from .auth import login_required
from .db import get_db

bp = Blueprint("avatar", __name__)

EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}
LADO_MAXIMO = 512          # a foto é redimensionada para, no máximo, 512x512
TAMANHO_MAX_MB = 5         # apenas para a mensagem ao usuário

CORES_PADRAO = ["#2563eb", "#16a34a", "#d97706", "#db2777", "#7c3aed", "#0891b2"]


def pasta_avatares():
    pasta = os.path.join(current_app.instance_path, "avatars")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def caminho_avatar(user_id):
    return os.path.join(pasta_avatares(), f"{user_id}.jpg")


def tem_avatar(user_id):
    return os.path.exists(caminho_avatar(user_id))


def _extensao_valida(nome_arquivo):
    if "." not in nome_arquivo:
        return False
    return nome_arquivo.rsplit(".", 1)[-1].lower() in EXTENSOES_PERMITIDAS


def _avatar_padrao(username):
    """Gera um avatar simples (círculo colorido com a inicial do nome)
    para usuários que ainda não enviaram uma foto."""
    inicial = (username[:1] or "?").upper()
    cor = CORES_PADRAO[sum(ord(c) for c in username) % len(CORES_PADRAO)]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<circle cx="50" cy="50" r="50" fill="{cor}"/>'
        '<text x="50" y="54" font-family="system-ui, sans-serif" font-size="46" '
        f'fill="#ffffff" text-anchor="middle" dominant-baseline="middle">{inicial}</text>'
        '</svg>'
    )
    resposta = Response(svg, mimetype="image/svg+xml")
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@bp.route("/perfil/foto", methods=("POST",))
@login_required
def enviar():
    destino = url_for("main.perfil")
    arquivo = request.files.get("foto")

    if arquivo is None or not arquivo.filename:
        flash("Selecione uma imagem para enviar.", "erro")
        return redirect(destino)

    if not _extensao_valida(arquivo.filename):
        flash("Formato não suportado. Envie uma imagem PNG, JPG, GIF ou WEBP.", "erro")
        return redirect(destino)

    # 1ª leitura: só confirma que é uma imagem válida (verify() não decodifica
    # os pixels, então o arquivo precisa ser reaberto para o uso real).
    try:
        imagem = Image.open(arquivo.stream)
        imagem.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        flash("O arquivo enviado não é uma imagem válida.", "erro")
        return redirect(destino)

    arquivo.stream.seek(0)
    try:
        imagem = Image.open(arquivo.stream)
        imagem = ImageOps.exif_transpose(imagem)  # corrige a rotação de fotos de celular
        imagem = imagem.convert("RGB")            # descarta transparência/paleta e GIFs animados
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        flash("Não foi possível processar a imagem enviada.", "erro")
        return redirect(destino)

    imagem.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
    imagem.save(caminho_avatar(g.user["id"]), format="JPEG", quality=85)

    flash("Foto de perfil atualizada.", "sucesso")
    return redirect(destino)


@bp.route("/avatar/<int:user_id>")
def exibir(user_id):
    usuario = get_db().execute(
        "SELECT username FROM usuarios WHERE id = ?", (user_id,)
    ).fetchone()
    if usuario is None:
        abort(404)

    caminho = caminho_avatar(user_id)
    if os.path.exists(caminho):
        # conditional=True faz o navegador reaproveitar o cache quando o
        # arquivo não mudou, e buscar de novo quando uma foto é substituída.
        return send_file(caminho, mimetype="image/jpeg", conditional=True, max_age=3600)

    return _avatar_padrao(usuario["username"])
