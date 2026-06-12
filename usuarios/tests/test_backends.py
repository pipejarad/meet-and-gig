"""
Regresión del hallazgo A3 (auditoría 11-06-2026).

EmailBackend hacía User.objects.get(Q(email__iexact=u) | Q(username__iexact=u)):
si el username de un usuario coincide con el email de otro, el get() devuelve
dos filas y lanza MultipleObjectsReturned (error 500). Como el validador por
defecto de Django permite '@' en usernames, un atacante podía registrarse con
username = email de la víctima y bloquearle el login.

Escrito como django.test.TestCase puro (sin fixtures de pytest) para correr
hoy con `manage.py test usuarios` y seguir siendo válido cuando el Bloque D
reconstruya la suite sobre pytest.
"""
from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase, override_settings

from usuarios.forms import RegistroForm

Usuario = get_user_model()

PASSWORD_VICTIMA = 'clave-segura-victima-7'
PASSWORD_ATACANTE = 'clave-segura-atacante-7'


def _crear_victima_y_atacante():
    """Reproduce el estado vulnerable saltándose el form (que tras el fix
    rechaza usernames con '@'): atacante con username == email de la víctima."""
    victima = Usuario.objects.create_user(
        username='victima',
        email='victima@example.com',
        password=PASSWORD_VICTIMA,
        tipo_usuario='musico',
    )
    atacante = Usuario.objects.create_user(
        username='victima@example.com',
        email='atacante@example.com',
        password=PASSWORD_ATACANTE,
        tipo_usuario='musico',
    )
    return victima, atacante


# AXES_ENABLED=False: estos tests son unitarios de EmailBackend y llaman
# authenticate() sin request, que el backend de axes (A4) no acepta. El
# bloqueo de fuerza bruta se cubre aparte en test_login_fuerza_bruta.py.
@override_settings(AXES_ENABLED=False)
class EmailBackendColisionTests(TestCase):
    """El backend debe resolver determinísticamente la colisión username/email."""

    def test_login_de_la_victima_no_lanza_excepcion_con_username_colisionante(self):
        victima, _ = _crear_victima_y_atacante()
        # Antes del fix: MultipleObjectsReturned → 500 y víctima bloqueada.
        user = authenticate(None, username='victima@example.com', password=PASSWORD_VICTIMA)
        self.assertEqual(user, victima)

    def test_password_incorrecta_devuelve_none_sin_excepcion_con_colision(self):
        _crear_victima_y_atacante()
        user = authenticate(None, username='victima@example.com', password='clave-incorrecta-1')
        self.assertIsNone(user)

    def test_el_match_por_email_tiene_prioridad_sobre_el_username(self):
        victima, atacante = _crear_victima_y_atacante()
        # El identificador 'victima@example.com' matchea el email de la víctima
        # Y el username del atacante: debe ganar el email (USERNAME_FIELD, único).
        user = authenticate(None, username='victima@example.com', password=PASSWORD_ATACANTE)
        self.assertIsNone(user)  # la clave del atacante no abre la cuenta de la víctima

    def test_el_atacante_sigue_pudiendo_entrar_con_su_propio_email(self):
        _, atacante = _crear_victima_y_atacante()
        user = authenticate(None, username='atacante@example.com', password=PASSWORD_ATACANTE)
        self.assertEqual(user, atacante)


@override_settings(AXES_ENABLED=False)
class EmailBackendBasicoTests(TestCase):
    """Comportamiento normal del backend, sin colisiones."""

    @classmethod
    def setUpTestData(cls):
        cls.musico = Usuario.objects.create_user(
            username='musico',
            email='musico@example.com',
            password=PASSWORD_VICTIMA,
            tipo_usuario='musico',
        )

    def test_login_por_email(self):
        self.assertEqual(
            authenticate(None, username='musico@example.com', password=PASSWORD_VICTIMA),
            self.musico,
        )

    def test_login_por_username(self):
        self.assertEqual(
            authenticate(None, username='musico', password=PASSWORD_VICTIMA),
            self.musico,
        )

    def test_identificador_inexistente_devuelve_none(self):
        self.assertIsNone(
            authenticate(None, username='nadie@example.com', password=PASSWORD_VICTIMA)
        )


class RegistroFormUsernameTests(TestCase):
    """Capa 2 del fix A3: el form de registro no debe permitir usernames que
    puedan hacerse pasar por el email de otra cuenta."""

    @classmethod
    def setUpTestData(cls):
        Usuario.objects.create_user(
            username='existente',
            email='existente@example.com',
            password=PASSWORD_VICTIMA,
            tipo_usuario='musico',
        )

    def _form(self, username):
        return RegistroForm(data={
            'username': username,
            'email': 'nuevo@example.com',
            'password1': 'clave-segura-nueva-7',
            'password2': 'clave-segura-nueva-7',
        })

    def test_username_con_arroba_es_rechazado(self):
        form = self._form('cualquiera@example.com')
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_username_igual_a_un_email_registrado_es_rechazado(self):
        form = self._form('existente@example.com')
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_username_normal_sigue_siendo_valido(self):
        form = self._form('musico_nuevo')
        self.assertTrue(form.is_valid(), form.errors)
