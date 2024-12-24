from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from promotional_marketing.models import PromotionalMessageTracker, send_whatsapp_on_save, PromotionalData
from import_export.admin import ImportExportModelAdmin
from django_admin_multi_select_filter.filters import MultiSelectFieldListFilter


class CustomAuthAdmin(admin.ModelAdmin):
    list_per_page = 20
    ordering = ('-updated_at',)

class PromotionalResource(resources.ModelResource):

    def after_save_instance(self, instance, using_transactions, dry_run):
        instance.dry_run = dry_run # set a temporal flag for dry-run mode
        super().after_save_instance(instance, using_transactions, dry_run)
        if dry_run is False:
            send_whatsapp_on_save(instance)



    class Meta:
        model = PromotionalMessageTracker

@admin.register(PromotionalMessageTracker)
class PromotionalMessageTrackerAdmin(CustomAuthAdmin,ImportExportModelAdmin):
    resource_class = PromotionalResource
    list_display = ["mobile_no","message_code", "is_purchased","last_purchase_date","message_sid","msg_status","send_force","updated_at","created_at"]
    search_fields = ("mobile_no", "message_code", "msg_status")
    list_filter = ['is_purchased','from_file',('msg_status', MultiSelectFieldListFilter),]


@admin.register(PromotionalData)
class PromotionalDataAdmin(CustomAuthAdmin):
    list_display = ["batch_size", "message_sent","send_all_at_once","is_data_imported","updated_at","created_at"]
    list_filter = ['send_all_at_once','is_data_imported',]
