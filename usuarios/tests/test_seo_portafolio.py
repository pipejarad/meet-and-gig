"""
Hallazgo C1 (auditoría 11-06-2026): JSON-LD del portafolio público.

El template construía el JSON a mano interpolando campo a campo: el
autoescape de Django convierte los & de las URLs en &amp; (sameAs corrupto →
Google descarta el structured data) y una ubicación nula se serializaba como
"None". Ahora el dict completo se construye en la vista y se serializa una
sola vez.
"""
import json
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Portafolio

Usuario = get_user_model()

INSTAGRAM_CON_AMPERSAND = 'https://www.instagram.com/labanda?igsh=abc&utm_source=qr'


class JsonLdPortafolioTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            username='pedroguitarra',
            email='pedro@example.com',
            password='clave-segura-7',
            tipo_usuario='musico',
            first_name='Pedro',
            last_name='Pérez',
        )
        cls.portafolio = Portafolio.objects.create(
            usuario=cls.usuario,
            activo=True,
            instagram_url=INSTAGRAM_CON_AMPERSAND,
            youtube_url='https://www.youtube.com/@labanda',
        )
        cls.url = reverse('ver_portafolio', kwargs={'slug': cls.portafolio.slug})

    def _json_ld(self):
        html = self.client.get(self.url).content.decode()
        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S
        )
        self.assertIsNotNone(match, 'No se encontró el bloque JSON-LD')
        return match.group(1)

    def test_es_json_valido_y_las_urls_no_se_corrompen(self):
        data = json.loads(self._json_ld())
        self.assertEqual(data['@type'], 'Person')
        self.assertEqual(data['name'], 'Pedro Pérez')
        # La URL debe llegar intacta: con autoescape, & se convierte en &amp;
        self.assertIn(INSTAGRAM_CON_AMPERSAND, data['sameAs'])
        self.assertIn('https://www.youtube.com/@labanda', data['sameAs'])

    def test_sin_ubicacion_no_se_emite_address_none(self):
        data = json.loads(self._json_ld())
        # El template viejo serializaba la ubicación nula como "None"
        self.assertNotEqual(
            data.get('address', {}).get('addressLocality'), 'None'
        )
