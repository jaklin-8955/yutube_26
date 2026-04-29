"""
WSGI config for yatube project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yatube.settings')

application = get_wsgi_application()
from django.shortcuts import render

def index(request):
    return render(request, 'posts/index.html')
