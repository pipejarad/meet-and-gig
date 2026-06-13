"""
Hallazgo C5 (auditoría 11-06-2026): social proof inversa en el home.

Mostrar "3 Músicos Registrados" comunica lo contrario de lo que se busca:
el bloque de estadísticas se oculta mientras no haya un mínimo de músicos
(UMBRAL_MUSICOS_PARA_ESTADISTICAS en usuarios/views.py).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.views import UMBRAL_MUSICOS_PARA_ESTADISTICAS

Usuario = get_user_model()


def _crear_musicos(cantidad):
    Usuario.objects.bulk_create([
        Usuario(
            username=f'musico{i}',
            email=f'musico{i}@example.com',
            tipo_usuario='musico',
        )
        for i in range(cantidad)
    ])


class SocialProofHomeTests(TestCase):

    def test_con_pocos_musicos_no_se_muestran_estadisticas(self):
        _crear_musicos(3)
        html = self.client.get(reverse('inicio')).content.decode()
        self.assertNotIn('Músicos Registrados', html)

    def test_con_el_umbral_alcanzado_si_se_muestran(self):
        _crear_musicos(UMBRAL_MUSICOS_PARA_ESTADISTICAS)
        html = self.client.get(reverse('inicio')).content.decode()
        self.assertIn('Músicos Registrados', html)
