from django.conf.urls import patterns, url
from hitstarter.apps.site import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^p/(?P<project_id>\d+)/.*?$', 'hitstarter.apps.site.views.project'),
    
)
