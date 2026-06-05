"""
Configuración de desarrollo local de Meet & Gig.
Uso: DJANGO_SETTINGS_MODULE=meetandgig.settings.development
"""
from .base import *  # noqa: F401, F403

# --------------------------------------------------------------------------
# Debug
# --------------------------------------------------------------------------
DEBUG = True

# En desarrollo, aceptar localhost por defecto aunque ALLOWED_HOSTS esté vacío
if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# --------------------------------------------------------------------------
# Base de datos — SQLite local
# --------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

# --------------------------------------------------------------------------
# Email — imprime en consola, no envía emails reales
# --------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@meetandgig.com')  # noqa: F405

SITE_URL = env('SITE_URL', default='http://127.0.0.1:8000')  # noqa: F405
