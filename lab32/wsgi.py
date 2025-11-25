import os

from django.core.wsgi import get_wsgi_application

# V V V V V V V V V V V V V V V V V V V V V V V V V V V V V V V V V
# THIS IS THE LINE THAT MUST BE "lab_3.2.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lab_3.2.settings")
# ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^

application = get_wsgi_application()