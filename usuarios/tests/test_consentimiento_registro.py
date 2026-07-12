"""
Hallazgo B2 (auditoría 11-06-2026): consentimiento explícito en el registro.

Checkbox obligatorio "He leído y acepto los Términos y la Política de
Privacidad" (con links a ambas páginas) y timestamp de aceptación en el
modelo Usuario (Ley 21.719: el consentimiento debe poder acreditarse).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.forms import RegistroForm

Usuario = get_user_model()

DATOS_VALIDOS = {
    'username': 'musiconuevo',
    'email': 'nuevo@example.com',
    'password1': 'clave-segura-nueva-7',
    'password2': 'clave-segura-nueva-7',
}


class ConsentimientoRegistroTests(TestCase):

    def test_sin_aceptar_terminos_el_form_es_invalido(self):
        form = RegistroForm(data=DATOS_VALIDOS)
        self.assertFalse(form.is_valid())
        self.assertIn('acepta_terminos', form.errors)

    def test_aceptando_terminos_el_form_es_valido(self):
        form = RegistroForm(data={**DATOS_VALIDOS, 'acepta_terminos': 'on'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_el_registro_guarda_el_timestamp_de_aceptacion(self):
        respuesta = self.client.post(
            reverse('registro'), {**DATOS_VALIDOS, 'acepta_terminos': 'on'}
        )
        self.assertEqual(respuesta.status_code, 302)
        usuario = Usuario.objects.get(email='nuevo@example.com')
        self.assertIsNotNone(usuario.terminos_aceptados_en)

    def test_la_pagina_de_registro_linkea_terminos_y_privacidad(self):
        respuesta = self.client.get(reverse('registro'))
        contenido = respuesta.content.decode()
        self.assertIn(reverse('terminos'), contenido)
        self.assertIn(reverse('privacidad'), contenido)
