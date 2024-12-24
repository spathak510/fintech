from rest_framework.views import APIView
from local_stores.serializers import LandinfPageUserSerializer, NavigantUsersDetailSerializer
from rest_framework.response import Response
from local_stores.utils import responsedata, welcome_notification_on_whatsapp
from rest_framework import permissions, status
from hv_whatsapp import settings as settings
from hv_whatsapp_api.hv_whatsapp_backend import whatsapp_backend_api

class StoreLandingPageUserInfo(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        data = request.data.copy()
        if not data.get('mobile_no'):  
            return Response(responsedata(False,"Mobile number is mindetery field." , 400),status=status.HTTP_400_BAD_REQUEST)         
        serializer = LandinfPageUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception =True):
            obj = serializer.save()
            mobile_no = '91'+str(data.get('mobile_no'))
            notification_send = welcome_notification_on_whatsapp(mobile_no)
            if not notification_send:
                obj.notification_status = False
                obj.save()
            return Response(responsedata(True,"Notification sent on your whats'app." , 200),status=status.HTTP_200_OK)
        
class StoreNavigantUserInfo(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        checks = {"Verify Nanny":"21","Verify Driver":"22","Verify Domestic Help/Security Guard":"23","Verify Anyone":"24","Know the Identity":"25","Know your Contact":"29" }
        data = request.data.copy()
        required_keys = ["mobile_num", "name", "source", "card", "sub_source", "price"]
        missing_or_empty_keys = [key for key in required_keys if key not in request.data or not request.data[key]]

        if request.data.get('source') not in settings.api_users:
            return Response(responsedata(False, "Authentication Failed for user {}".format(request.data.get('source')), code=401), status=status.HTTP_401_UNAUTHORIZED)                
        if missing_or_empty_keys:
            return Response(responsedata(False,f"Missing or empty keys: {', '.join(missing_or_empty_keys)}" , 400),status=status.HTTP_400_BAD_REQUEST)
        
        mobile_no = '91'+str(request.data.get('mobile_no'))
        appbackend = whatsapp_backend_api.Whatsapp_backend()
        service_type_id = checks[request.data.get('card')]
        redemption_pin = appbackend.get_redemption_pin(int(service_type_id), mobile_no)
        data['shared_redeempin'] = redemption_pin      
        serializer = NavigantUsersDetailSerializer(data=data)
        if serializer.is_valid(raise_exception =True):
            obj = serializer.save()
            resp = serializer.data
            return Response(responsedata(True, "Redeem pin generated for the given WhatsApp number   {}".format(obj.mobile_num), code=200, data=resp), status=status.HTTP_200_OK)                
        
class GeneratReedeemPin(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        try:
            print("hello..")
            appbackend = whatsapp_backend_api.Whatsapp_backend()
            service_type_id = 28
            mobile_no = "9411287010"
            redemption_pin = appbackend.get_redemption_pin(int(service_type_id), mobile_no)
            data = {"service_type":service_type_id,"redemption_pin":redemption_pin}
            return Response(responsedata(True, "Redeem pin generated successfully.", code=200, data=data), status=status.HTTP_200_OK) 
        except Exception as ex:
            return Response(responsedata(False, "Something went wrong in Redeem pin generation {}".format(str(ex)), code=400, data=data), status=status.HTTP_400_BAD_REQUEST) 
                
                    
                
