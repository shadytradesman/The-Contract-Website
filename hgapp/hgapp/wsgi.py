"""
WSGI config for hgapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os, traceback

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hgapp.settings")

try:
    application = get_wsgi_application()
    print('WSGI without exception')
except Exception:
    print("WSGI failed to load")
    traceback.print_exc()
    raise
