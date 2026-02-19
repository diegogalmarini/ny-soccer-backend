from __future__ import unicode_literals

from django.urls import re_path as url

from paypal.standard.pdt import views

urlpatterns = [
    url(r'^$', views.pdt, name="paypal-pdt"),
]
