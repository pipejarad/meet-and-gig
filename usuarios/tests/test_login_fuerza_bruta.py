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

    def test_menos_intentos_que_el_limite_no_bloquea(self):
        for _ in range(3):
            self._intento_fallido()

        respuesta = self.client.post(
            self.url, {'username': 'musico@example.com', 'password': PASSWORD_OK}
        )
        # Login exitoso → redirect
        self.assertEqual(respuesta.status_code, 302)
