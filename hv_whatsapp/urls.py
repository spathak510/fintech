"""hv_whatsapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
import hv_whatsapp_api
from hv_whatsapp_api import views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

urlpatterns = [
    path('',lambda request : HttpResponse("You are not permitted to access this webpage!")),
    path('hellov/', admin.site.urls),
    path('api/', include('hv_whatsapp_api.urls'), name="apis1"),
    path('ocr-apis/', include('ocr_apis.urls'), name="apis"),
    path('verification-apis/', include('verification_apis.urls'), name="apis"),
    path('external-apis/', include('external_apis.urls')),
    path('magic/', include('passwordless.urls'), name="magic"),
    path('payment/', include('hv_whatsapp_api.urls')),
    path('consent/', include('hv_whatsapp_api.urls')),
    path('case/', include('hv_whatsapp_api.urls')),
    path('report/', include('hv_whatsapp_api.urls')),
    path('stores/',include('local_stores.urls')),
    path('feedback/',include('feedback.urls')),
    path('ivr/',include('ivr_model.urls')),
] 
# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)