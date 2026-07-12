"""
Hallazgo A4 (auditoría 11-06-2026): protección de fuerza bruta en el login.

El bloqueo lo aporta django-axes: AXES_FAILURE_LIMIT intentos fallidos por
combinación usuario+IP → bloqueo temporal (AXES_COOLOFF_TIME). La combinación
evita que un atacante bloquee a una víctima desde otra IP (DoS de cuentas).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

Usuario = get_user_model()

PASSWORD_OK = 'clave-segura-musico-7'


class LoginFuerzaBrutaTests(TestCase):

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='musico',
            email='musico@example.com',
            password=PASSWORD_OK,
            tipo_usuario='musico',
        )
        self.url = reverse('login')

    def _intento_fallido(self):
        return self.client.post(
            self.url, {'username': 'musico@example.com', 'password': 'clave-mala-1'}
        )

    def test_al_quinto_intento_fallido_se_bloquea(self):
        for _ in range(4):
            respuesta = self._intento_fallido()
            self.assertEqual(respuesta.status_code, 200)  # vuelve al form con error

        # axes responde 429 Too Many Requests (default de axes 8)
        respuesta = self._intento_fallido()
        self.assertEqual(respuesta.status_code, 429)

    def test_bloqueado_ni_con_la_password_correcta_entra(self):
        for _ in range(5):
            self._intento_fallido()

        respuesta = self.client.post(
            self.url, {'username': 'musico@example.com', 'password': PASSWORD_OK}
        )
        self.assertEqual(respuesta.status_code, 429)

    def test_email_y_username_comparten_el_contador_de_bloqueo(self):
        # EmailBackend acepta email O username para la misma cuenta: si axes
        # contara cada cadena por separado, el atacante tendría el doble de
        # intentos (revisión adversarial del Bloque A). 4 fallos con el email
        # + 1 con el username deben caer en el MISMO cubo → bloqueo.
        for _ in range(4):
            self._intento_fallido()

        respuesta = self.client.post(
            self.url, {'username': 'musico', 'password': 'clave-mala-1'}
        )
        self.assertEqual(respuesta.status_code, 429)

    def test_la_pagina_de_bloqueo_no_acusa_credenciales_incorrectas(self):
        # El mensaje de error del form se encolaba antes de que el middleware
        # de axes cambiara la respuesta por el 429: la página de bloqueo decía
        # "Email o contraseña incorrectos" incluso con la contraseña correcta.
        for _ in range(5):
            self._intento_fallido()

        respuesta = self.client.post(
            self.url, {'username': 'musico@example.com', 'password': PASSWORD_OK}
        )
        self.assertEqual(respuesta.status_code, 429)
        self.assertNotIn('Email o contraseña incorrectos', respuesta.content.decode())

    def test_reintentar_durante_el_bloqueo_no_reinicia_la_espera(self):
        # El default de axes reinicia el cooloff con cada reintento durante el
        # bloqueo: el "espera una hora" del template nunca se cumpliría para
        # un usuario que insiste.
        from axes.models import AccessAttempt

        for _ in range(5):
            self._intento_fallido()
        marca_original = AccessAttempt.objects.get().attempt_time

        self._intento_fallido()
        self.assertEqual(AccessAttempt.objects.get().attempt_time, marca_original)

    def test_menos_intentos_que_el_limite_no_bloquea(self):
        for _ in range(3):
            self._intento_fallido()

        respuesta = self.client.post(
            self.url, {'username': 'musico@example.com', 'password': PASSWORD_OK}
        )
        # Login exitoso → redirect
        self.assertEqual(respuesta.status_code, 302)
