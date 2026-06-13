"""
Hallazgo C4 (auditoría 11-06-2026): sitemap.xml y robots.txt.

Sitemap con home, directorio de músicos y todos los portafolios activos
(lastmod = fecha_actualizacion). robots.txt permite todo salvo /admin/,
/mis-contactos/ y rutas privadas, y apunta al sitemap.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Portafolio

Usuario = get_user_model()


def _crear_portafolio(username, activo):
    usuario = Usuario.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='clave-segura-7',
        tipo_usuario='musico',
    )
    return Portafolio.objects.create(usuario=usuario, activo=activo)


class SitemapTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.publicado = _crear_portafolio('pedroguitarra', activo=True)
        cls.despublicado = _crear_portafolio('bateristaoculto', activo=False)

    def test_sitemap_responde_con_home_directorio_y_portafolios_activos(self):
        respuesta = self.client.get('/sitemap.xml')
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn(reverse('inicio'), contenido)
        self.assertIn(reverse('listar_portafolios'), contenido)
        self.assertIn(
            reverse('ver_portafolio', kwargs={'slug': self.publicado.slug}),
            contenido,
        )

    def test_los_portafolios_despublicados_no_aparecen(self):
        contenido = self.client.get('/sitemap.xml').content.decode()
        self.assertNotIn(self.despublicado.slug, contenido)

    def test_incluye_lastmod(self):
        contenido = self.client.get('/sitemap.xml').content.decode()
        self.assertIn('<lastmod>', contenido)


class RobotsTests(TestCase):

    def test_robots_permite_lo_publico_y_bloquea_lo_privado(self):
        respuesta = self.client.get('/robots.txt')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'text/plain')
        contenido = respuesta.content.decode()
        self.assertIn('Disallow: /admin/', contenido)
        self.assertIn('Disallow: /mis-contactos/', contenido)
        self.assertIn('Disallow: /cuenta/', contenido)
        self.assertIn('Sitemap: http://testserver/sitemap.xml', contenido)
