from django.urls import re_path, include
from django.conf import settings


urlpatterns = [
    re_path('', include(('base.utrls', 'base'), namespace='base')),
]


