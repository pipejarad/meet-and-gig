"""
Hallazgo D1 (auditoría 11-06-2026): suite de humo del embudo activo v1.

Cubre el contacto mediado y su embudo de estados, que son el corazón de la
vitrina (ROADMAP §5). El resto del embudo (registro→login→portafolio) ya
está cubierto por los tests de los Bloques A/B/C; aquí se completa lo que
faltaba: registro crea PerfilMusico atómicamente, contacto mediado
(creación, honeypot, rate limit, email con Reply-To) y el embudo de estados.
"""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from usuarios.models import ContactoMusico, PerfilMusico, Portafolio
from usuarios.views import LIMITE_CONTACTOS_POR_IP_HORA

Usuario = get_user_model()

PASSWORD = 'clave-segura-musico-7'
EMAIL_BACKEND_MEM = 'django.core.mail.backends.locmem.EmailBackend'


def _musico_con_portafolio(username='pedroguitarra', recibir_email=True):
    usuario = Usuario.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password=PASSWORD,
        tipo_usuario='musico',
    )
    perfil = PerfilMusico.objects.create(
        usuario=usuario, recibir_notificaciones_email=recibir_email
    )
    portafolio = Portafolio.objects.create(usuario=usuario, activo=True)
    return usuario, perfil, portafolio


class RegistroAtomicoTests(TestCase):
    """El registro crea Usuario + PerfilMusico juntos, o nada (D1)."""

    def _datos(self):
        return {
            'username': 'nuevomusico',
            'email': 'nuevo@example.com',
            'password1': 'clave-segura-nueva-7',
            'password2': 'clave-segura-nueva-7',
            'acepta_terminos': 'on',
        }

    def test_registro_crea_usuario_musico_y_su_perfil(self):
        respuesta = self.client.post(reverse('registro'), self._datos())
        self.assertEqual(respuesta.status_code, 302)
        usuario = Usuario.objects.get(email='nuevo@example.com')
        self.assertEqual(usuario.tipo_usuario, 'musico')
        self.assertTrue(PerfilMusico.objects.filter(usuario=usuario).exists())

    def test_si_falla_la_creacion_del_perfil_no_queda_usuario_huerfano(self):
        with mock.patch(
            'usuarios.views.PerfilMusico.objects.get_or_create',
            side_effect=RuntimeError('falla simulada'),
        ):
            self.client.post(reverse('registro'), self._datos())
        # El rollback de transaction.atomic no debe dejar el Usuario a medias
        self.assertFalse(Usuario.objects.filter(email='nuevo@example.com').exists())


@override_settings(EMAIL_BACKEND=EMAIL_BACKEND_MEM)
class ContactoMediadoTests(TestCase):
    """Contacto mediado: creación, honeypot, rate limit y email (D1)."""

    def setUp(self):
        self.usuario, self.perfil, self.portafolio = _musico_con_portafolio()
        self.url = reverse('contactar_musico', kwargs={'slug': self.portafolio.slug})

    def _datos(self, **extra):
        datos = {
            'remitente_nombre': 'Visitante Interesado',
            'remitente_email': 'visitante@example.com',
            'remitente_telefono': '+56999998888',
            'tipo_necesidad': 'evento',
            'mensaje': 'Hola, quiero contratarte para un matrimonio.',
        }
        datos.update(extra)
        return datos

    def test_contacto_valido_crea_registro_y_envia_email_con_reply_to(self):
        respuesta = self.client.post(self.url, self._datos())
        self.assertRedirects(
            respuesta, reverse('ver_portafolio', kwargs={'slug': self.portafolio.slug})
        )
        contacto = ContactoMusico.objects.get()
        self.assertEqual(contacto.musico, self.perfil)
        self.assertEqual(contacto.estado, ContactoMusico.Estado.ENVIADO)

        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, [self.usuario.email])
        self.assertEqual(correo.reply_to, ['visitante@example.com'])

    def test_honeypot_descarta_sin_guardar_ni_avisar(self):
        respuesta = self.client.post(self.url, self._datos(sitio_web='soy-un-bot'))
        # Responde como éxito para no darle pistas al bot…
        self.assertRedirects(
            respuesta, reverse('ver_portafolio', kwargs={'slug': self.portafolio.slug})
        )
        # …pero no guarda ni envía nada
        self.assertEqual(ContactoMusico.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limit_por_ip_corta_el_sexto_envio(self):
        ahora = timezone.now()
        for _ in range(LIMITE_CONTACTOS_POR_IP_HORA):
            ContactoMusico.objects.create(
                musico=self.perfil,
                remitente_nombre='Previo',
                remitente_email='previo@example.com',
                mensaje='previo',
                ip_remitente='127.0.0.1',  # la IP que reporta el test client
            )
        self.assertEqual(ContactoMusico.objects.count(), LIMITE_CONTACTOS_POR_IP_HORA)

        respuesta = self.client.post(self.url, self._datos())
        self.assertEqual(respuesta.status_code, 200)  # re-renderiza el form, no redirige
        # No se guardó el contacto número 6
        self.assertEqual(ContactoMusico.objects.count(), LIMITE_CONTACTOS_POR_IP_HORA)

    def test_si_el_musico_no_quiere_emails_no_se_envia(self):
        self.perfil.recibir_notificaciones_email = False
        self.perfil.save()
        self.client.post(self.url, self._datos())
        self.assertEqual(ContactoMusico.objects.count(), 1)  # el contacto SÍ se guarda
        self.assertEqual(len(mail.outbox), 0)                # el email NO se envía

    def test_no_se_puede_contactar_por_un_portafolio_inactivo(self):
        Portafolio.objects.filter(pk=self.portafolio.pk).update(activo=False)
        respuesta = self.client.post(self.url, self._datos())
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(ContactoMusico.objects.count(), 0)


class EmbudoEstadosTests(TestCase):
    """Embudo de estados: ENVIADO→VISTO al abrir el panel; RESPONDIDO/
    CONVERTIDO solo los marca el dueño (D1)."""

    def setUp(self):
        self.usuario, self.perfil, self.portafolio = _musico_con_portafolio()
        self.contacto = ContactoMusico.objects.create(
            musico=self.perfil,
            remitente_nombre='Visitante',
            remitente_email='visitante@example.com',
            mensaje='Hola',
        )

    def test_abrir_el_panel_pasa_enviado_a_visto(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('mis_contactos'))
        self.assertEqual(respuesta.status_code, 200)

        self.contacto.refresh_from_db()
        self.assertEqual(self.contacto.estado, ContactoMusico.Estado.VISTO)
        self.assertIsNotNone(self.contacto.visto_en)
        # El badge "Nuevo" se sigue mostrando en esta carga
        self.assertIn(self.contacto.id, respuesta.context['nuevos_ids'])

    def test_el_dueno_marca_convertido(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(
            reverse('marcar_contacto', kwargs={
                'contacto_id': self.contacto.id, 'nuevo_estado': 'convertido',
            })
        )
        self.assertEqual(respuesta.status_code, 302)
        self.contacto.refresh_from_db()
        self.assertEqual(self.contacto.estado, ContactoMusico.Estado.CONVERTIDO)

    def test_otro_musico_no_puede_marcar_un_contacto_ajeno(self):
        otro = Usuario.objects.create_user(
            username='otromusico', email='otro@example.com',
            password=PASSWORD, tipo_usuario='musico',
        )
        self.client.force_login(otro)
        respuesta = self.client.post(
            reverse('marcar_contacto', kwargs={
                'contacto_id': self.contacto.id, 'nuevo_estado': 'convertido',
            })
        )
        self.assertEqual(respuesta.status_code, 404)
        self.contacto.refresh_from_db()
        self.assertEqual(self.contacto.estado, ContactoMusico.Estado.ENVIADO)

    def test_estado_no_permitido_devuelve_404(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(
            reverse('marcar_contacto', kwargs={
                'contacto_id': self.contacto.id, 'nuevo_estado': 'enviado',
            })
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_marcar_por_get_no_cambia_estado(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(
            reverse('marcar_contacto', kwargs={
                'contacto_id': self.contacto.id, 'nuevo_estado': 'respondido',
            })
        )
        self.assertEqual(respuesta.status_code, 302)  # redirige sin tocar nada
        self.contacto.refresh_from_db()
        self.assertEqual(self.contacto.estado, ContactoMusico.Estado.ENVIADO)
