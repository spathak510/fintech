from django.contrib import admin
from external_apis.models import HitRecord

class CustomAuthAdmin(admin.ModelAdmin):
    list_per_page = 20
    ordering = ('-updated_at',)

class HitRecordAdmin(CustomAuthAdmin):
    list_display = ['user','api_name','api_endpoint','hit_time','payload','response']
admin.site.register(HitRecord,HitRecordAdmin)