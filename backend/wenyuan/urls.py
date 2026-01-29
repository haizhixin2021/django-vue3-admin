from django.urls import path
from rest_framework import routers
from wenyuan.views import ReadContentViewSet, ReadSignViewSet

route_url = routers.SimpleRouter()

route_url.register(r'read_content', ReadContentViewSet, basename='read_content')
route_url.register(r'read_sign', ReadSignViewSet, basename='read_sign')

urlpatterns = []
urlpatterns += route_url.urls
