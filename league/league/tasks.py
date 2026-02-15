# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task, Celery

app = Celery('nycs')

@shared_task
def test(x, y):
    return x + y

@app.task
def purge_outdated_payments():
    from league.models import PaymentPlaceholder
    print('####### Purging Unprocessed Payments ########')
    PaymentPlaceholder.purge_outdated()
    return 'Done'