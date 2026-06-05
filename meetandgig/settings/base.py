"""
Configuración base de Meet & Gig.
Compartida por todos los entornos. No usar directamente.
"""
from pathlib import Path
import environ

# BASE_DIR apunta a la raíz del proyecto (3 niveles arriba de este archivo)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Inicializar environ y leer .env si existe
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# --------------------------------------------------------------------------
# Seguridad — valores obligatorios desde variables de entorno
# --------------------------------------------------------------------------
SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# --------------------------------------------------------------------------
# Aplicaciones
# --------------------------------------------------------------------------
AUTH_USER_MODEL = 'usuarios.Usuario'

AUTHENTICATION_BACKENDS = [
    'usuarios.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
    'django.forms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meetandgig.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'meetandgig.wsgi.application'

# --------------------------------------------------------------------------
# Validación de contraseñas
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------------------------------
# Internacionalización
# --------------------------------------------------------------------------
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Archivos estáticos y multimedia
# --------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# En base (no en development): collectstatic en producción también debe
# recoger los estáticos del proyecto, no solo los del admin.
STATICFILES_DIRS = [
    BASE_DIR / 'meetandgig' / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Techo del cuerpo de requests no-archivo (defensa en profundidad; los
# archivos subidos se validan aparte con un máximo de 5MB en los forms)
DATA_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------
# URLs de autenticación
# --------------------------------------------------------------------------
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'inicio'
LOGOUT_REDIRECT_URL = 'login'

# --------------------------------------------------------------------------
# Asistente de IA del portafolio (ROADMAP §8)
# Sin API key, el asistente se desactiva con un mensaje amable (no rompe nada).
# --------------------------------------------------------------------------
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
BIO_IA_MODELO = env('BIO_IA_MODELO', default='claude-haiku-4-5')
