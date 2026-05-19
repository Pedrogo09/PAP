"""
WSGI config for bar_escola project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bar_escola.settings')

application = get_wsgi_application()
