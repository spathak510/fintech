# from django.conf.urls import url
from rest_framework import routers
from django.urls import include, path
from . import views as api_views


router = routers.DefaultRouter()
router.register('api', api_views.Views, basename = 'api')

urlpatterns = [
    path('', include(router.urls)),
]