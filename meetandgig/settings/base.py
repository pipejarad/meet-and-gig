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
    # axes va PRIMERO: corta el flujo de autenticación cuando hay bloqueo
    'axes.backends.AxesStandaloneBackend',
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
    'axes',
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
    'axes.middleware.AxesMiddleware',
]

# --------------------------------------------------------------------------
# django-axes — bloqueo de fuerza bruta en el login (auditoría A4)
# Usa la BD (AccessAttempt): consistente entre workers de gunicorn y entre
# deploys; no usar el handler de cache mientras no exista un cache compartido.
# --------------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5   # intentos fallidos antes de bloquear
AXES_COOLOFF_TIME = 1    # horas de bloqueo

# Bloquear por la combinación usuario+IP: bloquear solo por usuario dejaría
# que un atacante bloquee cuentas ajenas a propósito (DoS), y solo por IP
# castigaría a todos los que comparten una IP (NAT de universidad/oficina).
AXES_LOCKOUT_PARAMETERS = [['username', 'ip_address']]

AXES_RESET_ON_SUCCESS = True

# Sin esto (default True), cada reintento durante el bloqueo reinicia la
# hora de espera y el "espera una hora" de la página de bloqueo sería falso
# para cualquier usuario que insista.
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False

# El form de login envía la credencial como 'username' (email o username),
# pero axes por defecto la busca bajo el USERNAME_FIELD del modelo ('email')
# y registraría None. Ver usuarios.backends.identificador_para_axes.
AXES_USERNAME_CALLABLE = 'usuarios.backends.identificador_para_axes'

# Detrás del proxy de Railway, REMOTE_ADDR es la IP del proxy: sin esto, axes
# contaría los intentos de TODOS los visitantes contra la misma IP. Se
# reutiliza el helper del contacto mediado (única fuente de verdad de la IP).
AXES_CLIENT_IP_CALLABLE = 'usuarios.views._ip_del_request'

AXES_LOCKOUT_TEMPLATE = 'usuarios/login_bloqueado.html'

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
