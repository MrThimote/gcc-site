from celery import Celery
from django.conf import settings

app = Celery('gccsite')


app.conf.broker_transport_options = {'fanout_prefix': True}
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
