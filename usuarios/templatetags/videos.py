"""Filtro youtube_id (auditoría C2).

Extrae el ID de video de una URL de YouTube validando el dominio real. Vive
como filtro (y no como clean() del form) para cubrir también las URLs ya
guardadas en la BD sin migrar datos: el template decide en render si puede
embeber o cae al link plano.
"""
import re
from urllib.parse import parse_qs, urlparse

from django import template

register = template.Library()

# El ID de YouTube son 11 caracteres de este alfabeto; validar el formato
# garantiza además que el valor es seguro dentro del src del iframe.
ID_VALIDO = re.compile(r'^[A-Za-z0-9_-]{11}$')

DOMINIOS_YOUTUBE = {'youtube.com', 'm.youtube.com', 'music.youtube.com'}
PREFIJOS_PATH = ('/shorts/', '/embed/', '/live/')


@register.filter
def youtube_id(url):
    """ID del video si la URL es realmente de YouTube; '' en caso contrario."""
    if not url:
        return ''
    try:
        partes = urlparse(url)
    except ValueError:
        return ''

    host = (partes.hostname or '').lower()
    if host.startswith('www.'):
        host = host[4:]

    candidato = ''
    if host == 'youtu.be':
        candidato = partes.path.lstrip('/').split('/')[0]
    elif host in DOMINIOS_YOUTUBE:
        if partes.path == '/watch':
            candidato = parse_qs(partes.query).get('v', [''])[0]
        else:
            for prefijo in PREFIJOS_PATH:
                if partes.path.startswith(prefijo):
                    candidato = partes.path[len(prefijo):].split('/')[0]
                    break

    return candidato if ID_VALIDO.match(candidato) else ''
