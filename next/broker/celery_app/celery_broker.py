from __future__ import absolute_import
from celery import Celery


app = Celery('celery',
             include=['next.broker.celery_app.tasks'])

# Configuration file for the worker. The default values can be tnitialized from salt module
app.config_from_object('next.constants')

if __name__ == '__main__':
    app.start()
