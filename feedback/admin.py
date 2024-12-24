from django.contrib import admin
from feedback.models import VendorFeedback, FeedbackLinkValidation

class CustomAuthAdmin(admin.ModelAdmin):
    list_per_page = 20
    ordering = ('-updated_at',)

class VendorFeedbackAdmin(CustomAuthAdmin):
    list_display = ['order_id','overall_feddback','aditional_feedback','created_at','updated_at']
    ordering = ('-updated_at',)
    list_per_page = 20
    
    
    def order_id(self,request):
        return request.report_check.order_id
    
    
class FeedbackLinkValidationAdmin(CustomAuthAdmin):
    list_display = ['order_id','link_url','link_expired','created_at','updated_at'] 
    ordering = ('-updated_at',)
    list_per_page = 20 
    
    def order_id(self,request):
        return request.report_check.order_id  
    
    
    
    
admin.site.register(VendorFeedback,VendorFeedbackAdmin)
admin.site.register(FeedbackLinkValidation,FeedbackLinkValidationAdmin)