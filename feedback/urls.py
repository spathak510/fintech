from django.contrib import admin
from django.urls import path
from feedback import views

urlpatterns = [
    path('get-pre-feedback-details/<pk>',views.GetVendorFeedbackDetails.as_view()),
    path('save-feedback/',views.SaveVendorFeedback.as_view()),
] 