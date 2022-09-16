from django.urls import re_path
from .handlers import me

from .views import CategoryViewSet, EntityViewSet, OrderViewSet


urlpatterns = [
    re_path("^me$", me, name='self_info'),
    re_path(r"^cat/", CategoryViewSet, name='CategoryViewSet'),
    re_path(r"^ent/", EntityViewSet, name='EntityViewSet'),
    re_path(r"^ord/", OrderViewSet, name='OrderViewSet'),
]
