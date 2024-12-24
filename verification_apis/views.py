from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (DrivingLicenseVerificationSerializer, PANVerificationSerializer,
                            PassportVerificationSerializer, VoterIDVerificationSerializer, 
                            AadhaarVerificationSerializer, CriminalCheckSerializer, GetCriminalExternalCheckSerializer)
from .utils import (DLProcessor, PANProcessor, PassportProcessor, VoterIDProcessor, 
                    AadhaarProcessor, CriminalVerificationProcessor)
from hv_whatsapp_api.hv_whatsapp_backend.check_processor import BaseCheckProcessor
from hv_whatsapp_api.hv_whatsapp_backend import criminal_check_wrapper
from hv_whatsapp_api.models import criminal_result_external
import json

class DLVerification(APIView):
    'DL verification API'
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = DrivingLicenseVerificationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            source_api_response = DLProcessor().process(serializer.validated_data)
            DLProcessor().verify_driving_license_details(serializer.validated_data, source_api_response)
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)

class DLVerification1(APIView):
    'DL verification API'
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = DrivingLicenseVerificationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                source_api_response = DLProcessor().process(serializer.validated_data)
                DLProcessor().verify_driving_license_details(serializer.validated_data, source_api_response)
                serializer.save()
                return Response(serializer.data, status = status.HTTP_200_OK)
            except:
                return Response(data={"status": False,"message":"No data found for given details."},status=400)

class PANVerification(APIView):
    'PAN verification API'
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PANVerificationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            source_api_response = PANProcessor().process(serializer.validated_data)
            PANProcessor().verify_pan_details(serializer.validated_data, source_api_response)
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
class PassportVerification(APIView):
    'Passport verification API'
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PassportVerificationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            source_api_response = PassportProcessor().process(serializer.validated_data)
            PassportProcessor().verify_passport_details(serializer.validated_data, source_api_response)
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)

class VoterIDVerification(APIView):
    'VoterID verification API'
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = VoterIDVerificationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            source_api_response = VoterIDProcessor().process(serializer.validated_data)
            VoterIDProcessor().verify_voter_id_details(serializer.validated_data, source_api_response)
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)

class AadhaarVerification(APIView):
    'Aadhaar verification API'
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            serializer = AadhaarVerificationSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                source_api_response = AadhaarProcessor().process(serializer.validated_data)
                AadhaarProcessor().verify_aadhaar_details(serializer.validated_data, source_api_response)
                serializer.save()
                return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            import traceback, logging, inspect, datetime
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            logging.exception(str(source_api_response))
            return False


class CriminalVerification(APIView):
    'Criminal check API'
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CriminalCheckSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            response_status,resp = CriminalVerificationProcessor().process(serializer.validated_data)
            serializer.save()
            resp_data = serializer.data
            resp_data['order_id'] = resp['result']['order_id']
            return Response(resp_data, status = status.HTTP_200_OK)
        
        
class GetCriminalManualResponse(APIView):
    """
    Criminal check API
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        
        # Retrieve the most recent criminal external object for the order_id
        criminal_external_obj = criminal_result_external.objects.filter(order_id=pk).last()
        
        # Check if the object exists and contains the required fields
        if criminal_external_obj and criminal_external_obj.final_result_json and criminal_external_obj.manual_color_code:
            # Serialize the object data
            serializer = GetCriminalExternalCheckSerializer(criminal_external_obj)
            resp_data = serializer.data
            return Response(resp_data, status=status.HTTP_200_OK)
        
        # Return a structured error response if the object is not found
        error_response = {
            "error": "Manual result not found",
            "order_id": pk,
        }
        return Response(error_response, status=status.HTTP_404_NOT_FOUND)       

import requests
class DigilockerCallBack(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        BASE_URL = 'https://checkapi.helloverify.com'
        data = {
                "code": request.GET.get("code", None),
                "grant_type": "authorization_code",
                "client_id": "D1CA7F8E",
                "client_secret": "4a37db0a037422942f2f",
                # "client_secret": "50a3235ae5ae76f671fc",
                "redirect_uri": BASE_URL + "/verification-apis/digilocker/callback"
        }
        url = "https://api.digitallocker.gov.in/public/oauth2/1/token"
        res = requests.post(url, json=data)
        return Response(data={
                "status": True,
                "message": 'Data Retrieved Successfully',
                "data": {}
            })


class DigilockerData(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        BASE_URL = 'https://checkapi.helloverify.com'
        data = {
                "code": request.GET.get("code", None),
                "grant_type": "authorization_code",
                "client_id": "D1CA7F8E",
                "client_secret": "4a37db0a037422942f2f",
                # "client_secret": "ff72423dc200cf58bb9a",
                "redirect_uri": BASE_URL + "/verification-apis/digilocker/callback"
        }
        url = "https://api.digitallocker.gov.in/public/oauth2/1/token"
        res = requests.post(url, json=data)
        return Response(data={
                "status": True,
                "message": "Data Retrieved Successfully",
                "data": res.json()
            })



class ValuePitchToGetUpForChangeCriminalChekWrapper(APIView):
    'ValuePitch To GetUpForChange Criminal Chek wrapper API'
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        data = request.data
        if request.data['name'] and request.data['father_name'] and request.data['address']:
            search_term_json = request.data
            search_term_json['fatherName'] = data['father_name'] 
            valuepitch_res = BaseCheckProcessor().post_to_valuepitch_criminal(json.dumps(search_term_json))
            res = criminal_check_wrapper.transform_json(valuepitch_res)
            data['rule_engine_result'] = 'Not Check'
            data['source_api_response'] = json.dumps(res)
            serializer = CriminalCheckSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status = status.HTTP_200_OK)