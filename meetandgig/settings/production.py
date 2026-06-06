"""
Configuración de producción de Meet & Gig.
Uso: DJANGO_SETTINGS_MODULE=meetandgig.settings.production

Requiere las siguientes variables de entorno (ver .env.example):
  SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, DATABASE_URL,
  EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
  DEFAULT_FROM_EMAIL, SITE_URL
Opcionales (media en R2/S3 — sin ellas la media va al disco efímero):
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME,
  AWS_S3_ENDPOINT_URL
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
# Algunos proveedores usan SSL directo en el puerto 465 en vez de TLS/587
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)  # noqa: F405
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

# Railway termina TLS en su proxy y reenvía HTTP internamente. Sin esta
# cabecera, Django cree que cada request es insegura: SECURE_SSL_REDIRECT
# produce un bucle infinito de redirecciones y las cookies Secure no se fijan.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Django 4.2 exige el origen completo para aceptar POST sobre HTTPS detrás
# de proxy. Ej: https://meetandgig.up.railway.app,https://meetandgig.cl
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])  # noqa: F405

# --------------------------------------------------------------------------
# Archivos estáticos y media
# --------------------------------------------------------------------------
# Estáticos: WhiteNoise comprimido con manifest (el middleware está en base.py).
# Media: Cloudflare R2 (S3-compatible) vía django-storages — el disco de
# Railway es efímero. Si las variables AWS_* no están definidas, cae al
# almacenamiento local (solo aceptable para pruebas).
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

if env('AWS_STORAGE_BUCKET_NAME', default=''):  # noqa: F405
    STORAGES['default'] = {'BACKEND': 'storages.backends.s3.S3Storage'}
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')  # noqa: F405
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')  # noqa: F405
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')  # noqa: F405
    AWS_S3_ENDPOINT_URL = env('AWS_S3_ENDPOINT_URL')  # noqa: F405
    # R2 usa 'auto'; Backblaze B2 usa la región del endpoint (ej: us-west-004)
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='auto')  # noqa: F405
    AWS_S3_FILE_OVERWRITE = False      # no pisar archivos con el mismo nombre
    AWS_DEFAULT_ACL = None             # R2/B2 no usan ACLs por objeto

# --------------------------------------------------------------------------
# Logging — a stdout, que Railway captura. Sin esto, los errores 500 en
# producción no dejan rastro.
# --------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
