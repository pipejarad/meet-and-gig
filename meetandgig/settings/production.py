"""
Configuración de producción de Meet & Gig.
Uso: DJANGO_SETTINGS_MODULE=meetandgig.settings.production

Requiere las siguientes variables de entorno (ver .env.example):
  SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL,
  EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
  DEFAULT_FROM_EMAIL, SITE_URL
"""
from .base import *  # noqa: F401, F403

# --------------------------------------------------------------------------
# Debug — SIEMPRE False en producción
# --------------------------------------------------------------------------
DEBUG = False

# --------------------------------------------------------------------------
# Base de datos — PostgreSQL vía DATABASE_URL
# Ejemplo: postgres://usuario:password@host:5432/nombre_db
# --------------------------------------------------------------------------
DATABASES = {
    'default': env.db('DATABASE_URL')  # noqa: F405
}

# --------------------------------------------------------------------------
# Email — SMTP real
# --------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')  # noqa: F405
EMAIL_PORT = env.int('EMAIL_PORT', default=587)  # noqa: F405
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)  # noqa: F405
EMAIL_HOST_USER = env('EMAIL_HOST_USER')  # noqa: F405
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')  # noqa: F405
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')  # noqa: F405

SITE_URL = env('SITE_URL')  # noqa: F405

# --------------------------------------------------------------------------
# Seguridad adicional para producción
# --------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)  # noqa: F405
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
