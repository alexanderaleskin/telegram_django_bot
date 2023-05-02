from django.urls import re_path, include
from django.conf import settings

from .views import start, BotMenuElemViewSet, UserViewSet, some_debug_func


urlpatterns = [
    re_path('start', start, name='start'),
    re_path('main_menu', start, name='start'),

    re_path('sb/', BotMenuElemViewSet, name='BotMenuElemViewSet'),
    re_path('us/', UserViewSet, name='UserViewSet'),
]


if settings.DEBUG:
    urlpatterns += [
        re_path('some_debug_func', some_debug_func, name='some_debug_func'),
    ]