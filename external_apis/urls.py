from django.urls import path
from external_apis import views

urlpatterns = [
    path('verify-gst', views.VerifyGst.as_view(), name='verify-gst'),
    path('verify-mca', views.VerifyMca.as_view(), name='verify-mca'), 
    path('verify-email', views.EmailDomainVerification.as_view(), name='verify-email'), 
    path('verify-uan', views.UanVerification.as_view(), name='verify-uan'), 
    path('lexisnexis',views.LexisNexis.as_view(), name='lexisnexis'),
    path('pan-card', views.PanCustom.as_view(),name='pan-card'),
    path('verify-mobile', views.MobileVerificationWithoutOTP.as_view(), name='verify-mobile'),
    path('add-to-lat_long', views.LocationToLatLong.as_view(), name='add-to-lat_long'),
    path('compare-lat-long', views.CompareLatLong.as_view(), name='Comparell'),
    # score_me api below
    path('credit-rate-controller', views.CreditRateController.as_view(), name='credit-rate-controller'),
    path('company-info', views.CompanyInfo.as_view(), name='company-info'),
    # surepass aadhaar api
    path('verify-aadhaar', views.AadhaarCard.as_view(), name='verify-aadhaar'),
    # scoreme verify bank
    path('verify-bank-statement', views.BankStatementVerification.as_view(), name='verify-bank-statement'),
    path('verify-credit-balance-sheet', views.CreditBalanceSheet.as_view(), name='verify-credit-balance-sheet'),
    path('gst-info', views.Gstscore.as_view(), name='gst-info'),
    path('icwai-membership', views.IcwaiByk.as_view(), name='icwai-membership'),
    path('ca-membership', views.CaMembershipAuthByk.as_view(), name='ca-membership'),
    path('shop-establishment', views.ShopAndEstablishmentByk.as_view(), name='icwai-membership'),
    path('fssai-membership', views.FssaiAuthByk.as_view(), name='icwai-membership'),
    path('bank-verification', views.BankVerificationByk.as_view(), name='bank-verification'),
    path('udhyam-verification', views.UdyamRegCheckByk.as_view(), name='udhyam-verification'),
    path('lei', views.LEIByk.as_view(), name='lei'),
    path('itr', views.ITRAuthByk.as_view(), name='itr'),
    path('passport', views.PassportByk.as_view(), name='passport'),
    path('epf-comp', views.EpfByk.as_view(), name='epf-comp'),
    path('custom-orders', views.CustomOrderDetails),
    path('UAN',views.UANByK.as_view()),
    path("passport-ocr", views.PassportOCR.as_view(), name='passport-ocr'),
    path('gst-report', views.gstreport.as_view(), name = 'gstreport'),
    path('MCA-verification', views.McaByk.as_view(), name = 'mca-verification'),
    path('company-report-request', views.CompanyReportRequest.as_view(), name = 'companyreportrequest'),
    path('gst-report-request', views.GSTReportRequest.as_view(), name = 'gstreportrequest'),
    path('mca-signatories',views.MCASignatories.as_view(), name='mca_signatories'),
    path('passport_ocr_with_mrz_code',views.PassportOcrWithMrzCode.as_view(),name='passport_ocr_with_mrz_code'),
    path('pancard_ocr_code',views.PanCardOcr.as_view(),name='passport_ocr_code'),
    path('voter_ocr_code',views.VoterIdOcr.as_view(),name='voter_id_ocr_code'),
    path('dl_ocr_code',views.DLOcrCode.as_view(),name='dl_ocr_code'),
    path('aadhaar_ocr_code',views.AadhaarOcrCode.as_view(),name='aadhaar_ocr_code'),
    path('document_froud',views.DocumentFroud.as_view(),name='document_froud'),
    path('document_tempering_analysis',views.DocumentFroudResult.as_view(),name='document_froud_analysis_result'),

]