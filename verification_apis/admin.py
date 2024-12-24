from django.contrib import admin
from . import models as Model

# Register your models here.

class Admin_user(admin.ModelAdmin):
    readonly_fields=('created_at', 'updated_at')
    list_display = ["request_id","updated_at"]
    def has_module_permission(self, request):
        if request.user.username == 'admin':        
            return True
        return False

admin.site.register(Model.DrivingLicenseVerification, Admin_user)
admin.site.register(Model.AadhaarVerification, Admin_user)
admin.site.register(Model.VoterIDVerification, Admin_user)
admin.site.register(Model.PANVerification, Admin_user)
admin.site.register(Model.PassportVerification, Admin_user)
admin.site.register(Model.CriminalVerification, Admin_user)

