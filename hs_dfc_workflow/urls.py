from django.conf.urls import patterns, url
from hs_dfc_workflow import views

urlpatterns = patterns('',
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/execute_wso/$', views.execute_wso, name='execute_wso'),
)