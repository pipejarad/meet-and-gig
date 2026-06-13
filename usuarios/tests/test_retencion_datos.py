"""
Hallazgo B4 (auditoría 11-06-2026): retención de datos de ContactoMusico.

Command de retención (mismo patrón que marcar_invitaciones_expiradas, con
--dry-run): anonimiza ip_remitente a los 30 días del envío y elimina las
solicitudes de recuperación de contraseña antiguas (pendiente anotado por el
Bloque A). El plazo está documentado en la política de privacidad (B1).
"""
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from usuarios.models import (
    ContactoMusico, PerfilMusico, SolicitudRecuperacionPassword,
)

Usuario = get_user_model()


class RetencionDatosTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        usuario = Usuario.objects.create_user(
            username='pedroguitarra',
            email='pedro@example.com',
            password='clave-segura-7',
            tipo_usuario='musico',
        )
        cls.perfil = PerfilMusico.objects.create(usuario=usuario)

    def _contacto(self, dias_atras):
        contacto = ContactoMusico.objects.create(
            musico=self.perfil,
            remitente_nombre='Visitante',
            remitente_email='visita@example.com',
            mensaje='Hola, me interesa tu música.',
            ip_remitente='203.0.113.7',
        )
        # creado es auto_now_add: retrodatar vía update
        ContactoMusico.objects.filter(pk=contacto.pk).update(
            creado=timezone.now() - timedelta(days=dias_atras)
        )
        return contacto

    def _solicitud(self, dias_atras):
        solicitud = SolicitudRecuperacionPassword.objects.create(
            email='alguien@example.com', ip='203.0.113.7'
        )
        SolicitudRecuperacionPassword.objects.filter(pk=solicitud.pk).update(
            creado=timezone.now() - timedelta(days=dias_atras)
        )
        return solicitud

    def test_anonimiza_ips_de_contactos_con_mas_de_30_dias(self):
        viejo = self._contacto(dias_atras=31)
        reciente = self._contacto(dias_atras=5)

        call_command('aplicar_retencion_datos', stdout=StringIO())

        viejo.refresh_from_db()
        reciente.refresh_from_db()
        self.assertIsNone(viejo.ip_remitente)
        self.assertEqual(reciente.ip_remitente, '203.0.113.7')
        # El contenido del contacto se conserva: solo se anonimiza la IP
        self.assertEqual(viejo.remitente_email, 'visita@example.com')

    def test_elimina_solicitudes_de_recuperacion_antiguas(self):
        vieja = self._solicitud(dias_atras=31)
        reciente = self._solicitud(dias_atras=1)

        call_command('aplicar_retencion_datos', stdout=StringIO())

        pks = set(SolicitudRecuperacionPassword.objects.values_list('pk', flat=True))
        self.assertNotIn(vieja.pk, pks)
        self.assertIn(reciente.pk, pks)

    def test_dry_run_no_cambia_nada(self):
        viejo = self._contacto(dias_atras=31)
        vieja = self._solicitud(dias_atras=31)

        salida = StringIO()
        call_command('aplicar_retencion_datos', '--dry-run', stdout=salida)

        viejo.refresh_from_db()
        self.assertEqual(viejo.ip_remitente, '203.0.113.7')
        self.assertTrue(
            SolicitudRecuperacionPassword.objects.filter(pk=vieja.pk).exists()
        )
        self.assertIn('DRY RUN', salida.getvalue())
