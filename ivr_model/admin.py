from django.contrib import admin
from hv_whatsapp_api.models import order
from ivr_model.models import IVRCondidateTracker

class CustomAuthAdmin(admin.ModelAdmin):
    list_per_page = 20
    ordering = ('-updated_at',)

class IVRCondidateTrackerAdmin(CustomAuthAdmin):
    list_display = ['order_id','customer_lookup','is_processed','call_status','vendor_update','incomplete_report_send','incomplete_report_url']
    ordering = ('-updated_at',)
    list_per_page = 20
    
    
    def order_id(self,request):
        session_id = request.customer_lookup
        order_id = order.objects.filter(customer_info__session_id=session_id).last()
        return order_id.order_id 
    
    
    
    
admin.site.register(IVRCondidateTracker,IVRCondidateTrackerAdmin)