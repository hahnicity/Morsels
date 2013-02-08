from django.conf.urls.defaults import *
from morselsapp import views

urlpatterns = patterns('',
    #Upload / mymorsel handlers
    url(r'^upload/$', views.upload_media, name="upload_media"),
    url(r'^mymorsels/(?P<pk>\d+)/$', views.uploaded_mymorsel, name="uploaded_mymorsel"),
    url(r'^mymorsels/(?P<pk>\d+)/delete/$', views.delete_mymorsel, name="delete_mymorsel"),
    url(r'^mymorsels/(?P<pk>\d+)/delete/success/$', views.mymorsel_delete_callback, name="mymorsel_delete_callback"),
)
