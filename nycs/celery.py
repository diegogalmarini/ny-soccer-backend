from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nycs.settings')

app = Celery('nycs')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.

app.autodiscover_tasks()

@app.on_after_configure.connect
def periodic_tasks(sender, **kwargs):
    # Calls purge() every 10 minutes.
    from league.tasks import purge_outdated_payments
    sender.add_periodic_task(600.0, purge_outdated_payments.s(), name='purge every 10 minutes')


@app.task(bind=True)
def debug_task(self):
    print('###### Request: {0!r}'.format(self.request))