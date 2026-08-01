# Celery configuration file
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery application instance
app = Celery('config')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


# Debug task for testing
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """A debug task to verify Celery is working"""
    print(f'Request: {self.request!r}')
