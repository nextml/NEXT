"""
constants.py

author: Kevin Jamieson, kevin.g.jamieson@gmail.com, 
	Lalit Jain, lalitkumarj@gmail.com
last updated: 2/21/2015

Main configuration file for next_backend. Feel free to adjust by hand, but it
should be adjusted through docker environment variables.  To allow for fig
usage and docker linking, we use the enviroment variables available here:
http://docs.docker.com/userguide/dockerlinks/ Note that this forces us to run
redis and mongodb on 6379 and 27017. This seems to be best practice anyways.
"""
import os


# Variable to enable sites. This allows you to build clients and sites on the
# NEXT system.

SITES_ENABLED = False

# Backend Host Url
NEXT_BACKEND_GLOBAL_HOST = os.environ.get('NEXT_BACKEND_GLOBAL_HOST', None)
NEXT_BACKEND_GLOBAL_PORT = os.environ.get('NEXT_BACKEND_GLOBAL_PORT', '8000')

AWS_ACCESS_ID = os.environ.get('AWS_ACCESS_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')


MINIONREDIS_HOST = os.environ.get('MINIONREDIS_PORT_6379_TCP_ADDR', 'localhost')
MINIONREDIS_PORT = int(os.environ.get('MINIONREDIS_PORT_6379_TCP_PORT', 6379))
MINIONREDIS_PASS = os.environ.get('MINIONREDIS_ENV_REDIS_PASS', '')

# PermStore constants
MONGODB_HOST = os.environ.get('MONGODB_PORT_27017_TCP_ADDR','localhost')
MONGODB_PORT = int(os.environ.get('MONGODB_PORT_27017_TCP_PORT', 27017) )


# Database client constants
app_data_database_id = 'app_data'
logs_database_id = 'logs'
maxStringLengthInInspectDatabase = 200


RABBIT_HOSTNAME = os.environ.get('RABBIT_PORT_5672_TCP_ADDR', 'localhost')
RABBIT_PORT= int(os.environ.get('RABBIT_PORT_5672_TCP_PORT', 5672))

 
BROKER_URL = 'amqp://{user}:{password}@{hostname}:{port}/{vhost}/'.format(
    user=os.environ.get('RABBIT_ENV_RABBITMQ_USER', 'guest'),
    password=os.environ.get('RABBIT_ENV_RABBITMQ_PASS', 'guest'),
    hostname=RABBIT_HOSTNAME,
    port=RABBIT_PORT,
    vhost=os.environ.get('RABBIT_ENV_VHOST', ''))

RABBITREDIS_HOSTNAME = os.environ.get('RABBITREDIS_PORT_6379_TCP_ADDR', 'localhost')
RABBITREDIS_PORT = int(os.environ.get('RABBITREDIS_PORT_6379_TCP_PORT', 6379))
 

# https://github.com/celery/celery/issues/1909 describes the tradeoffs of redis and rabbitmq for results backend
CELERY_RESULT_BACKEND = 'redis://{hostname}:{port}/{db}/'.format(
    hostname=RABBITREDIS_HOSTNAME,
    port=RABBITREDIS_PORT,
    db=os.environ.get('RABBITREDIS_DB', '0'))
# CELERY_RESULT_BACKEND = BROKER_URL  
CELERY_TASK_RESULT_EXPIRES=60
CELERY_TASK_SERIALIZER='json'
CELERY_ACCEPT_CONTENT=['json']  # Ignore other content
CELERY_RESULT_SERIALIZER='json'
CELERYD_PREFETCH_MULTIPLIER=2

from kombu import Exchange, Queue
exchange_name = 'sync@{hostname}'.format(
        hostname=os.environ.get('HOSTNAME', 'localhost'))
sync_exchange = Exchange(name=exchange_name, type='fanout')

CELERY_SYNC_WORKER_COUNT = int(os.environ.get('CELERY_SYNC_WORKER_COUNT',1))
all_queues = ()
for i in range(1,CELERY_SYNC_WORKER_COUNT+1):
    queue_name = 'sync_queue_{worker_number}@{hostname}'.format(
        worker_number=i,
        hostname=os.environ.get('HOSTNAME', 'localhost'))
    all_queues += (Queue(name=queue_name,exchange=sync_exchange),)

CELERY_QUEUES = all_queues

