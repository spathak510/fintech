from django.contrib import admin
from django.forms import widgets
from django.utils.safestring import mark_safe
from local_stores.models import LandingPageUser, StoresModel, NavigantUsersDetail, PartnerUsersDetail

class CustomAuthAdmin(admin.ModelAdmin):
    list_per_page = 20
    ordering = ('-updated_at',)

class LandingPageUserAdmin(CustomAuthAdmin):
    list_display = ['name','mobile_no','created_at','updated_at','notification_status']
    

class StoresAdmin(CustomAuthAdmin):
    list_display = ['parent_id','name','mobile_num','email','branch_name','address','is_active']



   
class NavigantUsersDetailAdmin(CustomAuthAdmin):
    allowed_users = ['admin','PayTM','support']
    list_display = ['name','mobile_num','source','card','shared_redeempin','is_redeempin_redeemed','is_invite_sent_to_candidate','is_process_completed_by_candidate','is_report_share_to_client','created_at'] 
               
    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        else:
            return False
    def has_add_permission(self, request):
        # Disallow add permission
        return False

    def has_change_permission(self, request, obj=None):
        # Disallow change permission
        return False

    def has_delete_permission(self, request, obj=None):
        # Disallow delete permission
        return False

    def has_view_permission(self, request, obj=None):
        # Allow view permission
        return True

    def get_actions(self, request):
        # Remove the delete action from the actions list
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    
    
class PartnerUsersDetailAdmin(CustomAuthAdmin):
    allowed_users = ['admin','PayTM','support']
    list_display = ['shared_redeempin','mobile_num','source','sub_source','card','is_redeempin_redeemed','is_invite_sent_to_candidate','is_process_completed_by_candidate','is_report_share_to_client','created_at'] 
               
    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        else:
            return False
    def has_add_permission(self, request):
        # Disallow add permission
        return False

    def has_change_permission(self, request, obj=None):
        # Disallow change permission
        return False

    def has_delete_permission(self, request, obj=None):
        # Disallow delete permission
        return False

    def has_view_permission(self, request, obj=None):
        # Allow view permission
        return True

    def get_actions(self, request):
        # Remove the delete action from the actions list
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions        
    
    
    
admin.site.register(LandingPageUser,LandingPageUserAdmin)
admin.site.register(StoresModel,StoresAdmin)
admin.site.register(NavigantUsersDetail,NavigantUsersDetailAdmin)
admin.site.register(PartnerUsersDetail,PartnerUsersDetailAdmin)