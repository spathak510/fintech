import json
from django.urls import resolvers
from rest_framework import status, viewsets
from rest_framework.decorators import (action,   parser_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
import logging, traceback, inspect, requests
from datetime import datetime
from rest_framework.response import Response
from . import models as Model
from . import utils
# from fuzzywuzzy import fuzz
import hv_whatsapp.settings as app_settings
from .serializers import (AadhaarBackOcrSerializer, AadhaarFrontOcrSerializer, 
                            DrivingLicenseFrontSerializer, DrivingLicenseBackSerializer, 
                            VoterIDFrontSerializer, VoterIDBackSerializer, 
                            PassportIDFrontSerializer, PassportIDBackSerializer, PanOcrSerializer)

class Views(viewsets.ViewSet):
    
    # get DL details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_dl_front_detail(self, payload):
        try:
            payload = payload.data            
            api_obj = utils.DLApiBackend()
            result = api_obj.get_dl_front_result(payload['ocr_string'])

            if result != False:
                serializer = DrivingLicenseFrontSerializer(data=result)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response({'result': 'Invalid DL OCR String'}, status = status.HTTP_200_OK)
            return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get DL details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_dl_back_detail(self, payload):
        try:
            payload = payload.data            
            api_obj = utils.DLApiBackend()
            result = api_obj.get_dl_back_result(payload['ocr_string'])

            if result != False:
                serializer = DrivingLicenseBackSerializer(data=result)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response({'result': 'Invalid DL OCR String'}, status = status.HTTP_200_OK)
            return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get Voter ID details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_voter_front_detail(self, request):
        try:
            payload = request.data            
            api_obj = utils.VoterIDProcessor()
            result = api_obj.get_voter_front_result(payload['ocr_string'])

            if result != False:
                serializer = VoterIDFrontSerializer(data=result)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response({'result': 'Invalid OCR String'}, status = status.HTTP_200_OK)
            return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get Voter details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_voter_back_detail(self, request):
        try:
            payload = request.data
            api_obj = utils.VoterIDProcessor()
            result = api_obj.get_voter_back_result(payload['ocr_string'])

            if result != False:
                serializer = VoterIDBackSerializer(data=result)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response({'result': 'Invalid OCR String'}, status = status.HTTP_200_OK)    
            return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # get Passport ID details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_passport_front_detail(self, request):
        try:
            payload = request.data            
            api_obj = utils.PassportIDProcessor()
            result = api_obj.get_passport_front_result(payload['ocr_string'])
            if result != False:
                serializer = PassportIDFrontSerializer(data=result)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response({'result': 'Invalid OCR String'}, status = status.HTTP_200_OK)
            return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get Passport details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_passport_back_detail(self, request):
        try:
            payload = request.data
            api_obj = utils.PassportIDProcessor()
            result = api_obj.get_passport_back_result(payload['ocr_string'])

            if result != False:
                serializer = PassportIDBackSerializer(data=result)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response({'result': 'Invalid OCR String'}, status = status.HTTP_200_OK)    
            return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # get Aadhaar details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_aadhaar_front_detail(self, request):
        try:
            payload = request.data            
            api_obj = utils.AadhaarFrontProcessor()
            result = api_obj.process(payload['ocr_string'])
            if result != False:
                serializer = AadhaarFrontOcrSerializer(data=result)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response({'result': 'Invalid OCR String'}, status = status.HTTP_200_OK)
            return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get Aadhaar details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_aadhaar_back_detail(self, request):
        try:
            payload = request.data
            api_obj = utils.AadhaarBackProcessor()
            result = api_obj.process(payload['ocr_string'])

            if result != False:
                serializer = AadhaarBackOcrSerializer(data=result)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
            else:
                return Response({'result': 'Invalid OCR String'}, status = status.HTTP_200_OK)    
            return Response(serializer.data, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get PAN details from processor
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def parse_pan_detail(self, request):
        try:
            payload = request.data
            if payload['ocr_string'] and len(payload['ocr_string'])>5:
                api_obj = utils.PanOcrProcessor()
                result = api_obj.process(payload['ocr_string'])

                # if result != False:
                if result:
                    if 'pan_number' not in result:
                        return Response({'result': 'pan_number is not exist','data': payload}, status = status.HTTP_200_OK) 
                    
                    serializer = PanOcrSerializer(data=result)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        return Response(serializer.data, status = status.HTTP_200_OK)
                else:
                    return Response({'result': 'Invalid OCR String'}, status = status.HTTP_200_OK)    
            return Response({'result': 'Provide proper OCR String.'}, status = status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get OCR from processor
    # @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    # def fetch_id_ocr(self, request):
    #     try:
    #         file = request.data['file']
    #         image = UploadImageForOCR.objects.create(image=file)
    #         return Response({'ocr': 'okkk'}, status = status.HTTP_200_OK)
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)