"""
Hallazgo A4 (auditoría 11-06-2026): rate limit en la recuperación de contraseña.

Límite por email destino (3/hora) y por IP (5/hora) para impedir email
bombing, registrado en BD (SolicitudRecuperacionPassword) con el mismo patrón
del contacto mediado. Regla de oro: la respuesta al visitante es SIEMPRE la
misma — exista o no la cuenta, esté o no excedido el límite — para no romper
la protección anti-enumeración existente (al exceder, se degrada en silencio:
mismo mensaje, sin email).
"""
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from usuarios.models import SolicitudRecuperacionPassword

Usuario = get_user_model()

EMAIL_REGISTRADO = 'musico@example.com'


class RecuperacionPasswordRateLimitTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        Usuario.objects.create_user(
            username='musico',
            email=EMAIL_REGISTRADO,
            password='clave-segura-musico-7',
            tipo_usuario='musico',
        )

    def setUp(self):
        self.url = reverse('recuperar_password')

    def _solicitar(self, email, follow=False):
        return self.client.post(self.url, {'email': email}, follow=follow)

    @staticmethod
    def _mensajes(respuesta):
        """Mensajes renderizados en la página destino (requiere follow=True)."""
        return [str(m) for m in respuesta.context['messages']]

    def test_solicitud_normal_envia_email_y_queda_registrada(self):
        respuesta = self._solicitar(EMAIL_REGISTRADO)
        self.assertRedirects(respuesta, reverse('login'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(SolicitudRecuperacionPassword.objects.count(), 1)

    def test_email_inexistente_responde_identico_y_tambien_se_registra(self):
        respuesta_existente = self._solicitar(EMAIL_REGISTRADO, follow=True)
        respuesta_inexistente = self._solicitar('nadie@example.com', follow=True)

        self.assertEqual(
            respuesta_inexistente.redirect_chain, respuesta_existente.redirect_chain
        )
        self.assertEqual(
            self._mensajes(respuesta_inexistente), self._mensajes(respuesta_existente)
        )
        self.assertEqual(len(mail.outbox), 1)  # solo el de la cuenta real
        # Se registra SIEMPRE: si solo se registraran cuentas reales, el
        # conteo delataría qué emails existen.
        self.assertEqual(SolicitudRecuperacionPassword.objects.count(), 2)

    def test_cuarta_solicitud_al_mismo_email_no_envia_pero_responde_igual(self):
        primera = self._solicitar(EMAIL_REGISTRADO, follow=True)
        for _ in range(2):
            self._solicitar(EMAIL_REGISTRADO, follow=True)
        self.assertEqual(len(mail.outbox), 3)

        cuarta = self._solicitar(EMAIL_REGISTRADO, follow=True)
        self.assertEqual(cuarta.redirect_chain, primera.redirect_chain)
        self.assertEqual(self._mensajes(cuarta), self._mensajes(primera))
        self.assertEqual(len(mail.outbox), 3)  # degradación silenciosa
        self.assertEqual(SolicitudRecuperacionPassword.objects.count(), 4)

    def test_limite_por_ip_corta_aunque_los_emails_sean_distintos(self):
        # 5 solicitudes desde la misma IP a emails distintos agotan el cupo IP
        for i in range(5):
            self._solicitar(f'desconocido{i}@example.com')
        self.assertEqual(len(mail.outbox), 0)

        respuesta = self._solicitar(EMAIL_REGISTRADO)
        self.assertRedirects(respuesta, reverse('login'))
        self.assertEqual(len(mail.outbox), 0)  # bloqueado por IP, sin email
