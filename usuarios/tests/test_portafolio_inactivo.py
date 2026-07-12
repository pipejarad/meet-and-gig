"""
Complemento del hallazgo B3: un portafolio despublicado (activo=False) NO
debe servirse al público. Antes de este fix, la vista unificada ignoraba el
flag `activo` y mostraba portafolios despublicados con 200 — dejaba sin
efecto tanto el botón de despublicar como la eliminación de cuenta.

El dueño sí lo ve (vista previa de su propio portafolio despublicado).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Portafolio

Usuario = get_user_model()


class PortafolioInactivoTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.dueno = Usuario.objects.create_user(
            username='pedroguitarra',
            email='pedro@example.com',
            password='clave-segura-7',
            tipo_usuario='musico',
        )
        cls.portafolio = Portafolio.objects.create(usuario=cls.dueno, activo=False)
        cls.url = reverse('ver_portafolio', kwargs={'slug': cls.portafolio.slug})

    def test_visitante_recibe_404(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 404)

    def test_otro_usuario_logueado_tambien_recibe_404(self):
        otro = Usuario.objects.create_user(
            username='otromusico',
            email='otro@example.com',
            password='clave-segura-7',
            tipo_usuario='musico',
        )
        self.client.force_login(otro)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 404)

    def test_el_dueno_si_lo_ve(self):
        self.client.force_login(self.dueno)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
