from django.contrib import admin
from . import models as Model

# Register your models here.

class Admin_user(admin.ModelAdmin):
    readonly_fields=('created_at', 'updated_at')
    list_display = ["request_id","updated_at"]
    ordering = ('-updated_at', )

    def has_module_permission(self, request):
        if request.user.username == 'admin':        
            return True
        return False

admin.site.register(Model.DrivingLicenseOcrFront, Admin_user)
admin.site.register(Model.DrivingLicenseOcrBack, Admin_user)
admin.site.register(Model.PanOcr, Admin_user)
admin.site.register(Model.AadhaarOcrFront, Admin_user)
admin.site.register(Model.AadhaarOcrBack, Admin_user)
admin.site.register(Model.VoterIDOcrFront, Admin_user)
admin.site.register(Model.VoterIDOcrBack, Admin_user)
admin.site.register(Model.PassportIDOcrFront, Admin_user)
admin.site.register(Model.PassportIDOcrBack, Admin_user)
admin.site.register(Model.report_check, Admin_user)
