# from django.conf.urls import url
from rest_framework import routers
from hv_whatsapp_api.hv_whatsapp_backend import views as backend_views
from django.urls import include, path, re_path
from hv_whatsapp_api.hv_whatsapp_frontend import whatsapp_frontend_api
from . import views as api_views
from bank_statement_apis import views as bank_statement_views


router = routers.DefaultRouter()
router.register('whatsapp', backend_views.Views, basename = 'whatsapp')
router.register('frontend', whatsapp_frontend_api.Whatsapp_frontend, basename = 'whatsapp_frontend')
router.register('perfios', bank_statement_views.BankStatementViews, basename = 'bank_statement_apis')

urlpatterns = [
    path('', include(router.urls)),
    path('invoice/<str:url_id>', api_views.invoice),
    path('verify_now_invoice/<str:url_id>', api_views.verify_now_invoice),
    path('report/<str:sid>', api_views.report),
    path('incomplete_report/<str:sid>', api_views.incomplete_report),
    # path('page/<str:url_id>', api_views.index),
    # path('agreement/<str:url_id>', api_views.consent),
    # path('otp_process/', api_views.otp_process),
    # path('passbook_fetch/', api_views.passbook_fetch),
    # path('service_details_update/', api_views.service_details_update),
    path('generate_report/', api_views.generate_report),
    path('id_check_scheduler/', api_views.id_check_scheduler),
    path('index1/<str:sid>', api_views.index1),
    path('send_mesg_forcefully/', api_views.send_mesg_forcefully),
    path('cowin_report/<str:sid>', api_views.cowin_report),
    # path('pg/<int:year>/', year)
]