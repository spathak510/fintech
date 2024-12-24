from django.contrib import admin
from . import models as Model
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
import hv_whatsapp.settings as app_settings
from django_cron.models import CronJobLog
from rest_framework.authtoken.models import Token
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponse
import csv, io, logging, inspect, traceback
from import_export.admin import ImportExportModelAdmin
# from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
import datetime, json

class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
 
        meta = self.model._meta

        field_names = [field.name for field in meta.fields]
 
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)
 
        writer.writerow(field_names)
        for obj in queryset:
            obj.mobile_no = (obj.mobile_no).replace('+91','')
            row = writer.writerow([getattr(obj, field) for field in field_names])
 
        return response
 
    export_as_csv.short_description = "Export Selected"


# create model for admin order detail view
class OrderDetails(ImportExportModelAdmin ,admin.ModelAdmin):
    allowed_users = ['admin', 'shruti', 'abhinav', 'varun','amit']
    list_display = ["sid", "order_id", "mobile_no", "name",'package', "price", "promo_applied", "discount", "final_amount", "transaction_id","payment_recieved_date", 'auto_or_manual', 'final_status',"report_sent_time"]
    search_fields = ("order_id", "mobile_no", "transaction_id",) 
    list_per_page = 20
    ordering = ('-payment_recieved_date',)
    
    def sid(self, obj):
        return obj.customer_info.session_id

    def package(self, obj):
        service_obj = Model.service_detail.objects.filter(service_type_id = obj.customer_info.service_type_id, customer_type = obj.customer_info.customer_type).last()
        return str(service_obj.service_type_name)

    def promo_applied(self, obj):
        return obj.customer_info.promo_applied

    def discount(self, obj):
        if obj.customer_info.final_price:
            return int(obj.price) - int(obj.customer_info.final_price)
        else:
            return '--'
    
    def final_amount(self, obj):
        if obj.customer_info.final_price:
            return int(obj.customer_info.final_price)
        else:
            return '--'

    def get_queryset(self, request):
        if request.user.username == 'admin':
            exclude_list = []
        else:
            exclude_list = ['+919205264013', '+919205824013','+919928927887']
        qs = Model.order.objects.exclude(mobile_no__in=exclude_list)
        return qs

    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        
    def has_add_permission(self, request):
        if request.user.username == 'admin':
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if request.user.username == 'admin':
            context.update({
                'show_save': True,
                'show_save_and_continue': True,
                'show_delete': True
            })
            return super().render_change_form(request, context, True, True, form_url, obj)
        context.update({
        'show_save': False,
        'show_save_and_continue': False,
        'show_delete': False
    })
        return super().render_change_form(request, context, add, change, form_url, obj)

# create model for admin incomplete transaction detail view
class IncompleteTransactionDet(admin.ModelAdmin, ExportCsvMixin):
    allowed_users = ['admin', 'shruti', 'abhinav', 'varun']    
    list_display = ["mobile_no", "starts_with", "language_selected", "customer_type","package_name", "promo_applied", "id_uploaded", "last_message_time", "payment_link_status"]
    search_fields = ("mobile_no", )
    list_per_page = 20
    actions = ["export_as_csv"]

    # def sid(self, obj):
    #     return obj.customer_info.session_id

    def get_queryset(self, request):        
        if request.user.username == 'admin':
            exclude_list = []
        else:
            exclude_list = ['+919205264013', '+919205824013','+919811374026','+917532973604','+919928927887']
        qs = Model.AdminIncompleteTransactionModel.objects.exclude(mobile_no__in=exclude_list)
        return qs

    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True

    def has_add_permission(self, request):
        if request.user.username == 'admin':
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if request.user.username == 'admin':
            context.update({
                'show_save': True,
                'show_save_and_continue': True,
                'show_delete': True
            })
            return super().render_change_form(request, context, True, True, form_url, obj)
        context.update({
        'show_save': False,
        'show_save_and_continue': False,
        'show_delete': False
    })
        return super().render_change_form(request, context, add, change, form_url, obj)

# create model for admin consent detail view
class ConsentDetails(admin.ModelAdmin):
    allowed_users = ['admin', 'shruti', 'abhinav', 'varun']
    list_display = ["order_id","name", "mobile_number","consent_time"]
    search_fields = ("order_id", "name", "mobile_number", )
    list_per_page = 20

    # def sid(self, obj):
    #     return obj.order.customer_info.session_id

    def get_queryset(self, request):        
        if request.user.username == 'admin':
            exclude_list = []
        else:
            exclude_list = ['+919205264013', '+919205824013','+919928927887']
        qs = Model.consent.objects.exclude(mobile_number__in=exclude_list)
        return qs

    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        
    def has_add_permission(self, request):
        if request.user.username == 'admin':
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if request.user.username == 'admin':
            context.update({
                'show_save': True,
                'show_save_and_continue': True,
                'show_delete': True
            })
            return super().render_change_form(request, context, True, True, form_url, obj)
        context.update({
        'show_save': False,
        'show_save_and_continue': False,
        'show_delete': False
    })
        return super().render_change_form(request, context, add, change, form_url, obj)

# create model for admin consent detail view
class CustomerLookup(admin.ModelAdmin):
    allowed_users = ['admin', 'shruti','support']
    list_display = ["sid", "vendor_mobile","vendor_name", "candidate_mobile","candidate_name"]
    search_fields = ("sid", "vendor_mobile","vendor_name", "candidate_mobile","candidate_name")
    list_per_page = 20

    def sid(self, obj):
        return obj.customer_info.session_id

    def get_queryset(self, request):        
        if request.user.username == 'admin':
            exclude_list = []
        else:
            exclude_list = ['+919205264013', '+919205824013','+919928927887']
        qs = Model.customer_lookup.objects.exclude(vendor_mobile__in=exclude_list)
        return qs

    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        
    def has_add_permission(self, request):
        if request.user.username == 'admin':
            return True
        return False
    
    def has_view_permission(self, request, obj=None):
        # Allow view permission
        return True

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if request.user.username == 'admin':
            context.update({
                'show_save': True,
                'show_save_and_continue': True,
                'show_delete': True
            })
            return super().render_change_form(request, context, True, True, form_url, obj)
        context.update({
        'show_save': False,
        'show_save_and_continue': False,
        'show_delete': False
    })
        return super().render_change_form(request, context, add, change, form_url, obj)

class DlManualResponse(admin.ModelAdmin):
    fieldsets = [
                ('Fieldset', {'fields': ["order_id", "front_dl_image", 'back_dl_image', 'dl_number', 'name', 'father_name', 'address', 'issue_date',]}),
            ]
    readonly_fields = ("order_id", "front_dl_image", 'back_dl_image',)

    def has_module_permission(self, request):
        if request.user.username == 'manualuser' or request.user.username == 'admin':        
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

class Customer_session_info(admin.ModelAdmin):
    allowed_users = ['admin','support']
    list_display = ['customer_info', 'mobile_no', 'name', 'father_name', 'final_price', 'promo_applied']
    list_per_page = 500
    
    def has_module_permission(self, request):
        # if request.user.username == 'admin':
        if request.user.username in self.allowed_users:
            return True
        return False
    def has_view_permission(self, request, obj=None):
        # Allow view permission
        return True
    
    def customer_info(self, obj):
        return obj.session_id

class Admin_user(admin.ModelAdmin):
    def has_module_permission(self, request):
        if request.user.username == 'admin':        
            return True
        return False

class CustomerRegisterAdmin(Admin_user):
    search_fields = ['mobile_no']
    
class AdminVerifyNow(admin.ModelAdmin):
    allowed_users = ["admin", "shruti"]
    list_display = ["mobile_no","email","package_name", "transaction_number", \
        "transaction_captured" , "package_price", "discount", "final_amount", \
            "updated_at", "payment_received_date"]
    search_fields = ("mobile_no", "email") 
    # list_filter = ('transaction_captured',)
    ordering = ('-updated_at',)
    list_filter = (
        ('updated_at', DateTimeRangeFilter), 'transaction_captured'
    )

    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        else:
            return False

    def get_queryset(self, request):
        if request.user.username in self.allowed_users:
           qs = Model.VerifyNow.objects.exclude(mobile_no="+919205264013")
        return qs

    def has_add_permission(self, request):
        if request.user.username == 'admin':
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False
        
    def transaction_number(self, obj):
        if obj.transaction_id:
            return obj.transaction_id
        else:
            return '--'

    def package_name(self, obj):
        if obj.service_detail:
            return obj.service_detail.service_type_name.split(' - ')[0]
        else:
            return '--'

    def package_price(self, obj):
        if obj.service_detail:
            return obj.service_detail.service_type_price
        else:
            return '--'

    def final_amount(self, obj):
        if obj.service_detail:
            return obj.service_detail.service_type_price - obj.discount
        else:
            return '--'

    def payment_received_date(self, obj):
        if obj.transaction_captured:
            return obj.updated_at
        else:
            return '--'
    
class Ocr_response(admin.ModelAdmin):
    allowed_users = ['admin','support']
    list_display = ["session_id","show_front_url","show_back_url"]

    def has_module_permission(self, request):
        # if request.user.username == 'admin':
        if request.user.username in self.allowed_users:        
            return True
        return False
    def has_view_permission(self, request, obj=None):
        # Allow view permission
        return True

    def show_front_url(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.front_image_url)

    def show_back_url(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.back_image_url)
    
    def session_id(self, obj):
        return obj.customer_info.session_id

class Report_check(admin.ModelAdmin):
    allowed_users = ['admin','support']
    list_display = ["order_id", "report_status", "id_check_status", "crime_check_status", "emp_check_status", "show_report_url", "updated_at"]
    search_fields = ("order_id",)
    
    # def has_module_permission(self, request):
    #     if request.user.username == 'admin':        
    #         return True
    #     return False
    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        else:
            return False

    def has_change_permission(self, request, obj=None):
        # Disallow change permission
        return True

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

    def show_report_url(self, obj):
        report_name = 'Report_'+obj.order_id
        if obj.order.report_url:
            return format_html("<a href={url}>Report_PDF</a>", url=obj.order.report_url)
        else:
            return format_html("<a href='https://checkapi.helloverify.com/static/reports/{url}.pdf'>Report_PDFssss</a>", url=report_name)

class Api_hit_count(admin.ModelAdmin):
    list_display = ["order_id", "anti_captcha", "dl_api", "crime_api", "emp_api", "address_parser_api"]
    list_per_page = 20

    def has_module_permission(self, request):
        if request.user.username == 'admin':        
            return True
        return False
        
class Service_detail(admin.ModelAdmin):
    list_display = ["service_type_id", "service_type_name","service_type_price","final_price_in_words", "service_type_discount"]

    def has_module_permission(self, request):
        if request.user.username == 'admin':        
            return True
        return False

class Data_Backup(admin.ModelAdmin):
    list_display = ["file_url"]
    allowed_users = ['admin', 'shruti', 'abhinav', 'varun']

    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True

    def file_url(self, obj):
        return format_html("<a href='https://checkapi.helloverify.com/static/db_backup/{name}.csv'>{name}</a>", name=obj.file_name)

    def has_add_permission(self, request):
        if request.user.username == 'admin':
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if request.user.username == 'admin':
            context.update({
                'show_save': True,
                'show_save_and_continue': True,
                'show_delete': True
            })
            return super().render_change_form(request, context, True, True, form_url, obj)
        context.update({
        'show_save': False,
        'show_save_and_continue': False,
        'show_delete': False
    })
        return super().render_change_form(request, context, add, change, form_url, obj)

class Admin_user1(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ["order_id", "updated_at", "is_check_passed"]
    list_per_page = 20
    list_filter = (
        ('updated_at', DateTimeRangeFilter), 'is_check_passed'
    )
    def has_module_permission(self, request):
        if request.user.username == 'admin':
            return True
        return False

    def get_queryset(self, request):
        from datetime import date
        if request.user.username == 'admin':
           qs = Model.criminal_result_external.objects.all()
        return qs




class EduData(ImportExportModelAdmin, admin.ModelAdmin):
    allowed_users = ['admin', 'shruti', 'abhinav', 'vishal', 'varun']
    list_display = ["unique_id", "mobile_no", "name", "father_name", "tenth_doc", "twelveth_doc", "extra_doc", "case_status", "case_id", "is_twelveth", "msg_status", "updated_at"]
    # list_editable = ("case_status", "message_sent")
    search_fields = ("unique_id", "mobile_no", "name", "father_name") 
    list_filter = ('case_status',)
    list_per_page = 10
    
    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        return False

    def get_queryset(self, request):
        # from datetime import date
        if request.user.username in self.allowed_users:
           qs = Model.EducationData.objects.filter(hide_record = False)
        else:
            qs = Model.EducationData.objects.all()
        return qs
    
    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False
    
    def is_twelveth(self, obj):
        return str(obj.twelveth)

    def tenth_doc(self, obj):
        url = obj.tenth_url
        if url:
            return format_html("<a href={url}>Doc", url=url)
        else:
            return '-'

    def twelveth_doc(self, obj):
        url = obj.twelveth_url
        if url:
            return format_html("<a href={url}>Doc", url=url)
        else:
            return '-'

    def extra_doc(self, obj):
        if obj.extra_urls and len(obj.extra_urls) > 20:
            urls = (obj.extra_urls).split(',')
            i = 1
            extra_urls = ''
            print(urls)
            for url in urls:
                extra_urls = extra_urls + format_html("<a href={url}>Doc{i}", url=url, i=i) + ', '
                i = i + 1
            extra_urls = extra_urls[0:-2]
            return format_html(extra_urls)

    def has_add_permission(self, request):
        if request.user.username == 'admin':
            return True
        return False

    class Meta:
        model = Model.EducationData
        exclude = ('id',)

class CowinDetails(ImportExportModelAdmin, admin.ModelAdmin):
    allowed_users = ['admin', 'saurabh', 'shruti', 'cowin']
    list_display = ["check_id", "whatsapp_mobile_no", "cowin_mobile_no", "name", "vaccination_status", "cowin_report_url", "updated_at"]
    search_fields = ("check_id", "whatsapp_mobile_no", "cowin_mobile_no", "name")
    # list_filter = ('case_status',)
    list_per_page = 10

    def cowin_report_url(self, obj):
        url = obj.report_url
        if url:
            return format_html("<a href={url}>Report_URL", url=url)
        else:
            return '-'

    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        return False

    def get_queryset(self, request):
        if request.user.username in self.allowed_users:
           qs = Model.CowinData.objects.filter(hide_record = False)
        else:
            qs = Model.CowinData.objects.all()
        return qs
    
    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False


class NoBrokerAdmin(admin.ModelAdmin):
    allowed_users = ['admin', 'saurabh', 'shruti']
    list_display = ["order_id", "applicant_name", "package", "mobile_no", "email_id", "invite_sent_time"]
    list_per_page = 20
    search_fields = ("order_id", "name", "mobile_no", )

    def invite_sent_time(self, obj):
        return obj.created_at
        
    def get_queryset(self, request):        
        if request.user.username == 'admin':
            exclude_list = []
        else:
            exclude_list = ['+919205264013', '+919205824013','+919928927887']
        qs = Model.NobrokerOrder.objects.exclude(mobile_no__in=exclude_list)
        return qs

    def has_module_permission(self, request):
        if request.user.username in self.allowed_users:
            return True
        
    def has_add_permission(self, request):
        if request.user.username in self.allowed_users:
            return True

    def has_delete_permission(self, request, obj=None):
        if request.user.username == 'admin':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.username in self.allowed_users:
            return True

class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

class LatLongView(admin.ModelAdmin):
    list_display = ["request_id","candidate_name", "mobile_no", "distance", "is_match", "updated_at"]
    ordering = ('-updated_at',)
    list_per_page = 20
    list_filter = (
        ('updated_at', DateTimeRangeFilter), 'is_match'
    )

    # def get_queryset(self, request):        
    #     qs = Model.LatLong.objects.all()
    #     return qs

class VisaBankDetailView(admin.ModelAdmin):
    list_display = ["request_id", "bank_name", "updated_at"]
    ordering = ('-updated_at',)
    list_per_page = 20
    list_filter = (
        ('updated_at', DateTimeRangeFilter),
    )
    def get_queryset(self, request):        
        qs = Model.VisaBankDetail.objects.exclude(bank_name__isnull=True)
        return qs
    
class AdminSSLCheckDetails(admin.ModelAdmin):
    allowed_users = ['admin', 'saurabh', 'shruti']
    list_display = ['customer_info','selfie_url','signature_url','location_img_url']
    ordering = ('-updated_at',)
    list_per_page = 20 
    
# class AdminUniqueCodes(admin.ModelAdmin):
#     allowed_users = ['admin', 'saurabh']
#     list_display = ['id','customer_info','is_redeemed','service_type_id','code','mobile_no','redeem_time','is_distributed','transaction_id','partner_id']
#     search_fields = ('code','partner_id__name')
#     list_per_page = 20 
    
#     def has_module_permission(self, request):
#         if request.user.username in self.allowed_users:
#             return True      

admin.site.register(Model.AdminIncompleteTransactionModel,IncompleteTransactionDet)
admin.site.register(Model.consent, ConsentDetails)
admin.site.register(Model.VisaBankDetail, VisaBankDetailView)
admin.site.register(Model.dl_manual_response, DlManualResponse)
admin.site.register(Model.customer_info, Customer_session_info)
admin.site.register(Model.session_log, Admin_user)
admin.site.register(Model.service_detail, Service_detail)
admin.site.register(Model.ocr_response, Ocr_response)
admin.site.register(Model.customer_register, CustomerRegisterAdmin)
admin.site.register(Model.report_check, Report_check)
admin.site.register(Model.transaction_log, Admin_user)
admin.site.register(Model.dl_result, Admin_user)
admin.site.register(Model.customer_lookup, CustomerLookup)
admin.site.register(Model.question_master, Admin_user)
admin.site.register(Model.reminder, Admin_user)
admin.site.register(Model.adhaar_result, Admin_user)
admin.site.register(Model.report, Admin_user)
admin.site.register(Model.customer_coupon_code, Admin_user)
admin.site.register(Model.aadhaar_manual, Admin_user)
admin.site.register(Model.Dashboard, Data_Backup)
admin.site.register(Model.api_hit_count, Api_hit_count)
admin.site.register(Model.criminal_result, Admin_user)
admin.site.register(Model.uan_result, Admin_user)
admin.site.register(Model.order, OrderDetails)
admin.site.register(Model.criminal_result_external, Admin_user1)
# admin.site.register(Model.kyc_report_data, Admin_user)
# admin.site.register(Model.kyc_artifacts, Admin_user)
admin.site.register(Model.session_map, Admin_user)
admin.site.register(Model.LatLong, LatLongView)
admin.site.register(Model.CowinData, CowinDetails)
admin.site.register(Model.EducationData, EduData)
admin.site.register(Model.NobrokerOrder, NoBrokerAdmin)
admin.site.register(Model.EmailTemplate, Admin_user)
admin.site.register(Model.VerifyNow, AdminVerifyNow)
admin.site.register(Model.SSLChekDetails, AdminSSLCheckDetails)
# admin.site.register(Model.UniqueCodes, AdminUniqueCodes)


class QCAPILogView(admin.ModelAdmin):
    list_display = ["mob_no", "response_message","customer_info","request_type","created_at", "updated_at"]
    
    def response_message(self, request):
        try:
            return (eval(request.response)).get("Cards")[0].get("ResponseMessage")
        except:
            return "No Response"

    
    def request_type(self, request):
        try:
            if (eval(request.request_payload)).get("TransactionTypeId") == "302":
                return "Redeem Card"
            elif (eval(request.request_payload)).get("TransactionTypeId") == "306":
                return "Validate Redeem"
            else:
                return "Other"
        except:
            return "Some Error"


admin.site.register(Model.qc_api_log,QCAPILogView)
admin.site.register(Model.qc_auth_tokens)
admin.site.site_header = "HelloV Dashboard"
# admin.site.disable_action('delete_selected')
# admin.site.unregister(User)
# admin.site.unregister(Group)
# admin.site.unregister(CronJobLog)
# admin.site.unregister(Token)    
