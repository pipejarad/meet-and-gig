"""
Hallazgo B1 (auditoría 11-06-2026): páginas legales /terminos/ y /privacidad/.

Borradores marcados "PENDIENTE DE REVISIÓN LEGAL" (los revisará un abogado),
linkeados desde el footer de base.html y desde el registro.
"""
from django.test import TestCase
from django.urls import reverse


class PaginasLegalesTests(TestCase):

    def test_terminos_responde_y_es_borrador(self):
        respuesta = self.client.get(reverse('terminos'))
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn('PENDIENTE DE REVISIÓN LEGAL', contenido)
        self.assertIn('intermediario', contenido)  # NO empleador ni parte del contrato

    def test_privacidad_responde_y_es_borrador(self):
        respuesta = self.client.get(reverse('privacidad'))
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.content.decode()
        self.assertIn('PENDIENTE DE REVISIÓN LEGAL', contenido)
        self.assertIn('21.719', contenido)  # ley de protección de datos

    def test_el_footer_linkea_ambas_paginas(self):
        respuesta = self.client.get(reverse('inicio'))
        contenido = respuesta.content.decode()
        self.assertIn(reverse('terminos'), contenido)
        self.assertIn(reverse('privacidad'), contenido)
