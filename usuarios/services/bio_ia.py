"""Asistente de IA del portafolio — generación de borradores de biografía.

Servicio aislado (ROADMAP §8): la UI solo conoce `generar_bio(respuestas,
contexto_material)`. Cambiar de modelo o de proveedor se hace aquí, sin tocar
vistas ni templates.

Principios (CLAUDE.md):
- La IA produce un BORRADOR; el músico edita y aprueba. Nunca autopublicar.
- No inventar datos que el músico no entregó.
- Modelo económico (Claude Haiku), API key en variable de entorno
  (`ANTHROPIC_API_KEY`), límite de generaciones/día en la vista.

Forward-compat: el Modo 2 (contexto textual del material) y el Modo 3
(multimodal) solo cambian lo que alimenta `contexto_material`; la firma y la
UI no se mueven.
"""
import logging
import re

import anthropic
from django.conf import settings

logger = logging.getLogger('usuarios.bio_ia')

# 2 variantes de 80-120 palabras caben de sobra; también es el techo de costo.
MAX_TOKENS_RESPUESTA = 1000

SYSTEM = """Eres un periodista musical que escribe biografías de perfil
para una plataforma chilena que conecta músicos con quienes los contratan.
Escribe en español de Chile, tono profesional pero cercano, 80-120 palabras,
en tercera persona. Destaca lo que hace contratable al músico. Evita clichés.
Usa SOLO los datos entregados; si un dato falta, simplemente omítelo — no
inventes presentaciones, premios ni credenciales.
Devuelve exactamente DOS variantes de la biografía, separadas por una línea
que contenga únicamente tres guiones (---). Sin títulos, sin comillas, sin
numeración: solo el texto de cada biografía."""


class BioIAError(Exception):
    """Error al generar la biografía, con mensaje apto para mostrar al usuario."""


def generar_bio(respuestas, contexto_material=""):
    """Genera borradores de biografía (2 variantes) desde el formulario.

    `respuestas` es un dict con las claves del formulario estructurado
    (nombre, generos, formato, experiencia, destacados, eventos, unico).
    Devuelve una lista de 1-2 strings. Lanza BioIAError si falla.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise BioIAError(
            'El asistente de biografías no está disponible en este momento.'
        )

    material = f"- Material publicado: {contexto_material}\n" if contexto_material else ""
    prompt = f"""Datos del músico:
- Nombre artístico: {respuestas.get('nombre', '')}
- Géneros: {respuestas.get('generos', '')}
- Formato e instrumentos: {respuestas.get('formato', '')}
- Años de experiencia: {respuestas.get('experiencia', '')}
- Presentaciones destacadas: {respuestas.get('destacados', '')}
- Disponible para: {respuestas.get('eventos', '')}
- Qué lo hace único: {respuestas.get('unico', '')}
{material}
Escribe las dos variantes de la biografía."""

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    try:
        msg = client.messages.create(
            model=settings.BIO_IA_MODELO,
            max_tokens=MAX_TOKENS_RESPUESTA,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError:
        logger.exception('API key de Anthropic inválida o revocada')
        raise BioIAError('El asistente no está disponible en este momento.')
    except anthropic.RateLimitError:
        # El SDK ya reintentó con backoff (max_retries=2) antes de llegar aquí
        raise BioIAError('El asistente está ocupado. Intenta de nuevo en un minuto.')
    except anthropic.APIConnectionError:
        raise BioIAError('No pudimos conectar con el asistente. Intenta de nuevo.')
    except anthropic.APIStatusError as e:
        logger.exception('Error de la API de Anthropic (status %s)', e.status_code)
        raise BioIAError('El asistente falló. Intenta de nuevo en unos minutos.')

    texto = next((b.text for b in msg.content if b.type == 'text'), '')
    variantes = [v.strip() for v in re.split(r'\n\s*-{3,}\s*\n?', texto) if v.strip()]

    if not variantes:
        logger.error('La API respondió sin variantes utilizables: %r', texto[:200])
        raise BioIAError('El asistente no devolvió una biografía. Intenta de nuevo.')
    return variantes[:2]
