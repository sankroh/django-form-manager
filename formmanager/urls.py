from django.conf.urls.defaults import *
from models import ManagedForm 

urlpatterns = patterns('formmanager.views',
    url(r'^(?P<slug>[-\d\w]+)/export/$', 'export'),
    url(r'^(?P<slug>[-\d\w]+)/$', 'form_processor', name="managed_form_action"),
)


