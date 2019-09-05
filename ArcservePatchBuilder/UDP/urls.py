from django.conf.urls import url

from . import views
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?i)patches/(?P<patch>[tp]\d{8})/$', views.Share_patch, name='share_patch'),
]