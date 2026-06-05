"""
ASGI config for meetandgig project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Default seguro: igual que wsgi.py, los servidores entran por aquí.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meetandgig.settings.production')

application = get_asgi_application()
