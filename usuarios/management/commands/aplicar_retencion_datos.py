from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from usuarios.models import ContactoMusico, SolicitudRecuperacionPassword

# Plazo documentado en la política de privacidad (/privacidad/, sección 5).
# Si cambia, actualizar también esa página.
DIAS_RETENCION = 30


class Command(BaseCommand):
    help = (
        'Aplica la política de retención de datos (auditoría B4, Ley 21.719): '
        'anonimiza la IP de los contactos a los 30 días del envío y elimina '
        'las solicitudes de recuperación de contraseña con más de 30 días. '
        'Pensado para correr a diario vía cron de Railway: '
        'python manage.py aplicar_retencion_datos'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta en modo simulación sin realizar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        umbral = timezone.now() - timedelta(days=DIAS_RETENCION)

        # La IP del visitante solo sirve para el rate limit (ventana de 1 h);
        # se anonimiza pasado el plazo. El contenido del contacto NO se toca:
        # es el embudo de validación del músico.
        contactos = ContactoMusico.objects.filter(
            creado__lt=umbral, ip_remitente__isnull=False
        )
        # Las solicitudes de recuperación solo sostienen su rate limit (1 h);
        # pasado el plazo, la fila completa (email + IP) deja de ser necesaria.
        solicitudes = SolicitudRecuperacionPassword.objects.filter(creado__lt=umbral)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Se anonimizaría la IP de {contactos.count()} '
                    f'contacto(s) y se eliminarían {solicitudes.count()} '
                    f'solicitud(es) de recuperación'
                )
            )
            return

        anonimizados = contactos.update(ip_remitente=None)
        eliminadas, _ = solicitudes.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'IPs anonimizadas en {anonimizados} contacto(s); '
                f'{eliminadas} solicitud(es) de recuperación eliminada(s)'
            )
        )
