from django.urls import path
from verification_apis import views

urlpatterns = [
    path('dl-verification', views.DLVerification.as_view(), name='dl-verification'),
    path('dl-verification1', views.DLVerification1.as_view(), name='dl-verification1'),
    path('pan-verification', views.PANVerification.as_view(), name='pan-verification'), 
    path('passport-verification', views.PassportVerification.as_view(), name='passport-verification'), 
    path('voter-verification', views.VoterIDVerification.as_view(), name='voter-verification'), 
    path('aadhaar-verification', views.AadhaarVerification.as_view(), name='aadhaar-verification'), 
    path('criminal-verification', views.CriminalVerification.as_view(), name='criminal-verification'),
    path('get-criminal-manual-response/<pk>', views.GetCriminalManualResponse.as_view(), name='criminal-verification'), 
    path('digilocker/callback', views.DigilockerCallBack.as_view(), name='digilocker/callback'), 
    path('digilocker/get-data', views.DigilockerData.as_view(), name='digilocker/get-data'), 
    path('valuePitch-to-getUpForChange-wrapper',views.ValuePitchToGetUpForChangeCriminalChekWrapper.as_view(),name='ValuePitch-To-GetUpForChange-CriminalChek-Wrapper'),
]