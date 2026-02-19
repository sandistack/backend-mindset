"""
Celery configuration for Senior Collaboration Platform.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('config')

# Load config from Django settings with namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'cleanup-expired-invites': {
        'task': 'apps.workspaces.tasks.cleanup_expired_invites',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'aggregate-daily-activity': {
        'task': 'apps.activity.tasks.aggregate_daily_activity',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'send-digest-emails': {
        'task': 'apps.notifications.tasks.send_digest_emails',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
