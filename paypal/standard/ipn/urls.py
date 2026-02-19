from __future__ import unicode_literals

from django.urls import re_path as url

from paypal.standard.ipn import views

urlpatterns = [
    url(r'^$', views.ipn, name="paypal-ipn"),
]
