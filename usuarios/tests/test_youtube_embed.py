"""
Hallazgo C2 (auditoría 11-06-2026): embed de video frágil.

El template usaba slice posicional ('17:'/'32:') que solo funcionaba con dos
formatos exactos de URL. El filtro youtube_id extrae el ID validando el
dominio real; si no puede, el template cae al link plano como antes.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Portafolio
from usuarios.templatetags.videos import youtube_id

Usuario = get_user_model()


class YoutubeIdFiltroTests(TestCase):
    """Unidad: extracción del ID en los formatos reales de YouTube."""

    def test_formatos_validos(self):
        casos = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://youtube.com/watch?v=dQw4w9WgXcQ',            # sin www
            'http://m.youtube.com/watch?v=dQw4w9WgXcQ',           # móvil
            'https://music.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s',  # params extra
            'https://youtu.be/dQw4w9WgXcQ',
            'https://youtu.be/dQw4w9WgXcQ?si=AbCdEfGhIjKlMnOp',   # share link
            'https://www.youtube.com/shorts/dQw4w9WgXcQ',
            'https://www.youtube.com/embed/dQw4w9WgXcQ',
            'https://www.youtube.com/live/dQw4w9WgXcQ',
        ]
        for url in casos:
            with self.subTest(url=url):
                self.assertEqual(youtube_id(url), 'dQw4w9WgXcQ')

    def test_no_youtube_devuelve_vacio(self):
        casos = [
            'https://vimeo.com/123456',
            'https://noesyoutube.com/watch?v=dQw4w9WgXcQ',
            'https://youtube.com.malicioso.cl/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/@canal',     # canal, no video
            'no es una url',
            '',
            None,
        ]
        for url in casos:
            with self.subTest(url=url):
                self.assertEqual(youtube_id(url), '')

    def test_id_malformado_devuelve_vacio(self):
        # El ID de YouTube tiene 11 caracteres [A-Za-z0-9_-]: cualquier otra
        # cosa no debe terminar dentro del src del iframe.
        self.assertEqual(youtube_id('https://youtu.be/"><script>x</script>'), '')
        self.assertEqual(youtube_id('https://www.youtube.com/watch?v=corto'), '')


class EmbedEnPortafolioTests(TestCase):
    """Integración: el portafolio embebe el video o cae al link plano."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            username='pedroguitarra',
            email='pedro@example.com',
            password='clave-segura-7',
            tipo_usuario='musico',
        )
        cls.portafolio = Portafolio.objects.create(usuario=cls.usuario, activo=True)
        cls.url = reverse('ver_portafolio', kwargs={'slug': cls.portafolio.slug})

    def test_url_de_youtube_compartida_se_embebe(self):
        # Formato real del botón "compartir" de YouTube: rompía el slice viejo
        Portafolio.objects.filter(pk=self.portafolio.pk).update(
            video_demo='https://youtu.be/dQw4w9WgXcQ?si=AbCdEfGhIjKlMnOp'
        )
        html = self.client.get(self.url).content.decode()
        self.assertIn('https://www.youtube.com/embed/dQw4w9WgXcQ', html)

    def test_video_no_youtube_cae_al_link_plano(self):
        Portafolio.objects.filter(pk=self.portafolio.pk).update(
            video_demo='https://vimeo.com/123456'
        )
        html = self.client.get(self.url).content.decode()
        self.assertNotIn('youtube.com/embed', html)
        self.assertIn('https://vimeo.com/123456', html)
