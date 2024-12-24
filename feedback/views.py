from feedback import models as Model
from hv_whatsapp_api.models import report_check, service_detail, customer_lookup
from rest_framework.views import APIView
from local_stores.utils import responsedata
from rest_framework.response import Response
from rest_framework import permissions, status
from hv_whatsapp_api.hv_whatsapp_backend import whatsapp_backend_api, processor




# Send feedback link to the vendor after deliverd to the report
def send_feedback_link(report_check_instance):
    order_id = report_check_instance.order_id
    # vendor_mobile_num = report_check_instance.order.customer_info.mobile_no
    session_id = report_check_instance.order.customer_info.session_id
    lookup_obj = customer_lookup.objects.filter(customer_info = session_id).last()
    vendor_mobile_num = lookup_obj.vendor_mobile
    # url_link ='Would you kindly share your thoughts on the following link?/n'+ 'https://hellov.in/app/' + order_id
    url_link ='https://www.hellov.in/feedback/?order_id=' + order_id
    feedback_link_validation_obj = Model.FeedbackLinkValidation.objects.filter(report_check__order_id=order_id).last()    
    if not feedback_link_validation_obj:
        feedback_link_validation_obj = Model.FeedbackLinkValidation()
        feedback_link_validation_obj.report_check = report_check_instance
        feedback_link_validation_obj.link_url = url_link
        feedback_link_validation_obj.save()
        send_msg = processor.DB_Processor()
        send_msg.sent_reminder(vendor_mobile_num, url_link)
        return True
    return False
        
    


class GetVendorFeedbackDetails(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, pk):
        try:
            print('GetVendorFeedbackDetails.....')
            feedback_link_expiry_obj = Model.FeedbackLinkValidation.objects.filter(report_check__order_id=pk).last()
            if feedback_link_expiry_obj.link_expired == True:
                return Response(responsedata(False,"Link expired!." , 200),status=status.HTTP_200_OK)
            report_check_obj = report_check.objects.filter(order_id=pk).last()
            if report_check_obj:
                customer_info_obj = report_check_obj.order.customer_info
                service_type_id =  customer_info_obj.service_type_id
                service_detail_obj = service_detail.objects.filter(service_type_id=service_type_id).last()
                data = {
                "service_name" : service_detail_obj.service_type_name.split('-')[0],
                "client_name" : customer_info_obj.name,
                "mobile_no" : customer_info_obj.mobile_no,
                "date" : customer_info_obj.created_at
                }
                return Response(responsedata(True,"Data retrived successfully." , 200, data=data),status=status.HTTP_200_OK)
        except Exception as ex:
            return Response(responsedata(False,str(ex) , 400),status=status.HTTP_400_BAD_REQUEST)
        
        
class SaveVendorFeedback(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        try:
            print('SaveVendorFeedback.....')
            if not request.data.get('overall_feddback') and not request.data.get('order_id'):
                return Response(responsedata(False,"Overall_feddback is required field." , 400),status=status.HTTP_400_BAD_REQUEST)
            feedback_link_validation_obj = Model.FeedbackLinkValidation.objects.filter(report_check__order = request.data.get('order_id')).last()
            if feedback_link_validation_obj and feedback_link_validation_obj.link_expired != True:
                Model.VendorFeedback.objects.create(report_check=feedback_link_validation_obj.report_check,overall_feddback=request.data.get('overall_feddback'),aditional_feedback=request.data.get('aditional_feedback'),status=True)
                feedback_link_validation_obj.link_expired = True
                feedback_link_validation_obj.save()
                return Response(responsedata(True,"Your feedback save successfully." , 200),status=status.HTTP_200_OK)
        except Exception as ex:
            return Response(responsedata(False,str(ex) , 400),status=status.HTTP_400_BAD_REQUEST)        

