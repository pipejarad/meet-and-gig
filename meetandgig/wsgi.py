"""
WSGI config for meetandgig project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Default seguro: gunicorn (producción) entra por aquí. Si falta el entorno,
# es mejor que falle pidiendo SECRET_KEY a que arranque con DEBUG y SQLite.
# El desarrollo local usa manage.py, cuyo default es settings.development.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meetandgig.settings.production')

application = get_wsgi_application()
