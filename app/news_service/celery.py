import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_service.settings')

app = Celery('news_service')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Simple file-based scheduler configuration
app.conf.beat_schedule = {
    'fetch-articles-hourly': {
        'task': 'fetchers.tasks.fetch_articles_task',
        'schedule': 3600,  # Run every hour (3600 seconds)
        'options': {
            'expires': 3000,  # Task expires after 50 minutes if not picked up
        },
    },

}

# Use file-based scheduler (simpler, no database required)
app.conf.beat_scheduler = 'celery.beat:PersistentScheduler'
app.conf.beat_schedule_filename = 'celerybeat-schedule'

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')