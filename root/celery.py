import logging
import os

from celery import Celery

# Set default settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings.development")

app = Celery("root")

# Suppress noisy Celery logger warnings
logging.getLogger("celery.utils.functional").setLevel(logging.WARNING)
logging.getLogger("celery.app.trace").setLevel(logging.WARNING)

# Load configuration namespaces
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks from all apps
app.autodiscover_tasks()
