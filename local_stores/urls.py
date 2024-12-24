from django.urls import path
from local_stores import views

urlpatterns = [
    path('save-user-info/',views.StoreLandingPageUserInfo.as_view()),
    path('case-initiate/',views.StoreNavigantUserInfo.as_view()),
    path('generat-reedeem-pin/',views.GeneratReedeemPin.as_view())
    
]