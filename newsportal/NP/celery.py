import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NP.settings')
app = Celery('NP')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'every_monday_message': {
        'task': 'NewsPortal.tasks.every_monday_message',
        'schedule': crontab(),#hour=8, minute=0, day_of_week='monday'
    },
}

app.conf.timezone = 'UTC'
app.autodiscover_tasks()