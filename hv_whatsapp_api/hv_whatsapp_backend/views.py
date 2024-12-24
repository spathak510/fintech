import json, os, uuid, base64, re, time, cv2
# from braintree import Customer
from django.http import HttpResponse
# import pandas as pd
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import get_object_or_404, render
from rest_framework import serializers as RestSerializers
from rest_framework import status, viewsets
import rest_framework
from rest_framework.decorators import (action,   parser_classes)
from rest_framework.parsers import FileUploadParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.renderers import (JSONRenderer, StaticHTMLRenderer, TemplateHTMLRenderer)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
# from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.views.decorators.csrf import csrf_exempt
from . import check_processor as check_processors
from hv_whatsapp import settings as app_settings
from hv_whatsapp_api import models as Model
from django.utils.timezone import utc
from . import report as rpt
import datetime
from django.db.models import Q
from selenium.webdriver.common.keys import Keys
import time
from hv_whatsapp_api.hv_whatsapp_backend.captcha import GetCaptcha
from . import models
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
from . import captcha
from hv_whatsapp_api.hv_whatsapp_backend import whatsapp_backend_api, processor, report, send_mail
from hv_whatsapp_api import views
import pdfkit
import traceback
from retrying import retry
from datetime import datetime
from io import BytesIO
from django.core.files import File
from . import processor as pr
import requests
from django.core.cache import cache
from django.db import IntegrityError
import logging
import inspect

import base64
from hashlib import md5
import threading
import razorpay
from Cryptodome import Random
from Cryptodome.Cipher import AES
from local_stores.utils import update_cantidate_notification_for_strors, update_cantidate_notification_for_partners

BLOCK_SIZE = 16

logging.basicConfig(filename="error_log.log")



class Views(viewsets.ViewSet):

    def pad(self, data):
        length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
        return data + (chr(length)*length).encode()

    def unpad(self, data):
        return data[:-(data[-1] if type(data[-1]) == int else ord(data[-1]))]

    def bytes_to_key(self, data, salt, output=48):
        assert len(salt) == 8, len(salt)
        data += salt
        key = md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = md5(key + data).digest()
            final_key += key
        return final_key[:output]

    def encrypt(self, message, passphrase):
        salt = Random.new().read(8)
        key_iv = self.bytes_to_key(passphrase, salt, 32+16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return base64.b64encode(b"Salted__" + salt + aes.encrypt(self.pad(message)))

    def decrypt(self, encrypted, passphrase):
        encrypted = base64.b64decode(encrypted)
        assert encrypted[0:8] == b"Salted__"
        salt = encrypted[8:16]
        key_iv = self.bytes_to_key(passphrase, salt, 32+16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return self.unpad(aes.decrypt(encrypted[16:]))

    # get Adhaar details from processor
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_adhaar_results(self, payload):
        try:
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)
            process = check_processors.AdhaarValidationProcessor()
            res = process.process(check_model)
            return res
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # get Driving License details from processor
    # @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_dl_results(self, payload):
        
        try: 
            # session_id = payload.data['session_id']
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)
            process = check_processors.DrivingLicenseProcessor()
            sts, res = process.process(check_model)
            return Response(json.loads(res), status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    '''
    get dl manual result after the manual submit
    '''
    def get_dl_manual_results(self, payload):
        
        try: 
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)
            process = check_processors.DrivingLicenseManualProcessor()
            sts, res = process.process(check_model)
            return Response(json.loads(res), status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get Voter ID details from processor
    # @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    # def get_voter_results(self, request):
        
    #     try:
    #         data = request['data']

    #         if 'voter_id' in data:
    #             voter_id = data['voter_id']

    #             process = VoterProcessor()
    #             sts, res = process.process(voter_id)
    #             return Response(json.loads(res), status = status.HTTP_200_OK)
    #         else:
    #             return Response(False, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get PAN details from processor
    # @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    # def get_pan_results(self, request):
    #     try:
    #         data = request['data']
    #         data = json.loads(data)
    #         if 'pan' in data:
    #             pan = data['pan']
    #             pan_process = PANProcessor()#.process(pan)
    #             sts,res = pan_process.process(pan)
    #             return Response(json.loads(res), status = status.HTTP_200_OK)
    #         else:
    #             return Response(False, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # get Crime Check details from processor
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_crimecheck_results(self, payload):
        try:
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)
            crime_process = check_processors.CrimeCheckProcessor()
            sts,res = crime_process.process(check_model)
            return Response(json.loads(res), status = status.HTTP_200_OK)

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

        # get Crime Check details from processor
    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
    def get_crimecheck_results_extern(self, request):
        try:
            claimed_data = request.data
            if 'dob' not in claimed_data or len(claimed_data['dob']) != 10:
                return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
            order_id_data = Model.criminal_result_external.objects.filter(order_id = claimed_data['order_id']).last()
            if order_id_data and claimed_data['existing_record']:
                return Response({'result': json.loads(order_id_data.final_result_json)}, status = status.HTTP_200_OK)
            elif order_id_data:
                return Response({'result': 'order_id already processed. To fetch the existing record send request parameter "existing_record": true'}, status = status.HTTP_200_OK)
            elif claimed_data['existing_record']:
                return Response({'result': 'Not found any existing record with the provided order ID'}, status = status.HTTP_200_OK)
            crime_process = check_processors.CrimeCheckProcessor()
            sts,res = crime_process.process_external(claimed_data)
            if sts:
                
                return Response({'result': res}, status = status.HTTP_200_OK)
            else:
                return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_uan_results(self, payload):
        try:
            # payload = payload.data
            uan_process = check_processors.DigitalEmploymentCheckProcessor()
            # payload = payload.data            
            res = uan_process.fetch_uan_data(payload)
            
            return {'result': res}
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_uan_key(self):
        try:
            uan_process = check_processors.DigitalEmploymentCheckProcessor()
            # payload = payload.data            
            res = uan_process.get_uan_key()
            
            return Response({'apiKey': res}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    '''
    call anticaptcha for addhar verification
    '''
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_adhaar_verification_results(self, request):

        try:
            url = "https://resident.uidai.gov.in/verify"
            headers = {
                "Host": "resident.uidai.gov.in",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-Type": "application/x-www-form-urlencoded",
                "Content-Length": 135,
                "Origin": "https://resident.uidai.gov.in",
                "Connection": "keep-alive",
                "Referer": "https://resident.uidai.gov.in/verify",
                "Cookie": "PHPSESSIONID=ChKVGXkQBQpKQt4WU1vJeQ$$; PHPSESSID=pn2m5qebs5eofmqtttrj8989s7",
                "Upgrade-Insecure-Requests": 1
            }
            request_body = "uidno=512436964865&security_code=rphsr&form_action=Proceed+to+Verify&task=verifyaadhaar&boxchecked=0&c597d422d5bb72782694abe33b327dc5=1"

            res = requests.post(url = url, headers = headers, data = request_body )
            return Response(json.loads(res), status = status.HTTP_200_OK) 
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Adhaar front api call
    #@action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_adhaar_front_results(self, payload):

        try:
            data = payload#request['data']

            if 'ocr_string' in data:
                adhaar_front_process = check_processors.AdhaarFrontAddressProcessor()#.process(pan)
                res = adhaar_front_process.process(data["ocr_string"])

                return res
            else:
                return Response(False, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Adhaar back api call
    #@action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_adhaar_back_results(self, payload):

        try:
            cust_obj = Model.customer_info.objects.get(session_id = payload['session_id'])
            data = payload#request['data']
            #check back and front image from same aadhaar or not
            input_str = data["ocr_string"].lower().replace('\n', ' ')
            
            if 'ocr_string' in data:
                adhaar_back_process = check_processors.AdhaarBackAddressProcessor()#.process(pan)
                res = adhaar_back_process.process(data["ocr_string"])
                return res
            else:
                False
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    # DL front api call
    #@action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_dl_front_results(self, payload):

        try:
            data = payload#request['data']
            if 'ocr_string' in data:
                dl_front_process = check_processors.DLFrontProcessor()#.process(pan)
                res = dl_front_process.process(data["ocr_string"])

                return res
            else:
                return Response(False, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Adhaar back api call
    #@action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_dl_back_results(self, payload):

        try:
            data = payload#request['data']

            if 'ocr_string' in data:
                adhaar_back_process = check_processors.DLBackProcessor()#.process(pan)
                res = adhaar_back_process.process(data["ocr_string"])

                return res
            else:
                return Response(False, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    '''
    NOT IN USE
    '''
    # @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    # def make_payment(self, request):

    #     try:
    #         data = request.data

    #         if 'name' in data:

    #             name = data['name']
    #             amount = data['amount']
    #             cid = data['cid']

    #             payment_process = PaymentProcessor()#.process(pan)
    #             sts,res = payment_process.process(name, amount, cid)

    #             return Response(res, status = status.HTTP_200_OK)
    #         else:
    #             return Response(False, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    '''
    NOT IN USE
    '''
    #@action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def send_mobile_otp(self, payload):

        try:
            session_id = payload["session_id"]

            mobile_process = check_processors.MobileOTPProcessor()
            mobile_otp = mobile_process.send_otp(session_id)
            
            return mobile_otp#Response(res, status = status.HTTP_200_OK)
            
        except Exception as ex:            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Generate and send mobile otp
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def send_mobile_otp_frontend(self, request):
        password = "qwerty@98765".encode()
        try:
            # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
            #     data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            # else:
            data = request.data
            json_str = {}
            url_id = data["url_id"]
            # if api hit from dav frontend 
            # if data.get('dav'):                
            #     order_obj = Model.order.objects.filter(order_id=url_id).last()
            #     session_id = order_obj.customer_info.session_id
            # else:
            map_model = Model.session_map.objects.filter(url_id=url_id).last()
            session_id = map_model.customer_info.session_id
            mobile_process = check_processors.MobileOTPProcessor()
            mobile_otp = mobile_process.send_otp(session_id)
            json_str["url_id"] = url_id 
            if mobile_otp != '':
                json_str["otp_send"] = True
            else:
                json_str["otp_send"] = False            
            
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_200_OK)            
        except Exception as ex:            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            json_str = {}
            json_str["otp_send"] = False
            json_str["url_id"] = url_id
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    '''
    NOT IN USE
    '''
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_mobile_otp(self, payload):

        try:
            session_id = payload["session_id"]
            otp = payload['otp']

            otp_process = check_processors.VerifyMobileOTPProcessor()#.process(pan)
            res = otp_process.process(session_id, otp)
            
            return Response(res,status = status.HTTP_200_OK)
            
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # check the coupon code validity before payment
    def check_coupon_validity(self, session_id):
        try:
            cust_model = Model.customer_info.objects.get(session_id=session_id)
            mobile_no = cust_model.mobile_no

            
            unique_code_check = Model.UniqueCodes.objects.filter(mobile_no = mobile_no, is_redeemed = False).last()

            if unique_code_check or cust_model.customer_type == '3' or (cust_model.payment_status and cust_model.gift_card):
                return True
                    
            return False

        except Exception as ex:
            traceback.print_exc()
            # logging.warning("<----------"+str(datetime.now())+"---------->")
            # logging.exception((inspect.currentframe().f_code.co_name).upper())

    '''
    check url validity before is_url-valid to check whether url expire or not
    '''
    def check_url_validity(self, url_id):
        try:
            url_expire_model = Model.url_expiry.objects.filter(url_id = url_id).last()

            if url_expire_model:
                customer_type = url_expire_model.customer_info.customer_type

                if customer_type == '3':
                    return url_expire_model.expired
            
                # get time of sending url 
                db_time = url_expire_model.url_send_time
                db_time = db_time.replace(tzinfo=None)
                now = datetime.now().replace(tzinfo=None)
                timediff = now - db_time
                time_diff = timediff.total_seconds()//60

                if time_diff > 30:
                    return True  # true means url is expired
                else:
                    return url_expire_model.expired
            else:
                return True
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def apply_promo(self, request):
        password = "qwerty@98765".encode()
        try:
            # appbackend = whatsapp_backend_api.Whatsapp_backend()
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            else:
                data = request.data

            json_str = {}
            check_model = Model.session_map.objects.get(url_id = data["url_id"])            
            session_id = check_model.customer_info.session_id                
            cust_obj = Model.customer_info.objects.get(session_id = session_id)
            service_obj = Model.service_detail.objects.filter(service_type_id = cust_obj.service_type_id, customer_type = cust_obj.customer_type).last()
            
            promocode = data["promo"].upper()
            gpromocode_obj = Model.GeneralPromoCodes.objects.filter(code = promocode, is_expired = False).last()
            if gpromocode_obj:                
                cust_obj.final_price = int(service_obj.service_type_price * (1 - gpromocode_obj.discount_percentage/100))
                cust_obj.promo_applied = gpromocode_obj.code                
                json_str['msg'] = "Promo code successfully applied. Your final package price is ₹" + str(cust_obj.final_price)
            else:
                cust_obj.final_price = service_obj.service_type_price
                cust_obj.promo_applied = '--'
                json_str['msg'] = 'Invalid Promo Code Applied'            
            cust_obj.save()
                
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            json_str = {}
            json_str['msg'] = 'Invalid Promocode Applied'
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # check whether url session is valid?
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def is_url_valid(self, request):
        password = "qwerty@98765".encode()
        try:
            # appbackend = whatsapp_backend_api.Whatsapp_backend()
            # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
            #     data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            # else:
            data = request.data
            #print"Data",data, type(data))
            json_str = {}
            url_id = data.get("url_id", None)
            if not url_id:
                json_str['is_valid'] = "Fail"
                if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:    
                    json_str = json.dumps(json_str)            
                    json_str = self.encrypt(json_str.encode(), password)
                return Response(json_str, status = status.HTTP_200_OK)
            url_expire = self.check_url_validity(url_id)

            if url_expire and url_id != 'mmv6gYGk':
                json_str['is_valid'] = "Fail"
                if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                    json_str = json.dumps(json_str)
                    json_str = self.encrypt(json_str.encode(), password)
                return Response(json_str, status = status.HTTP_200_OK)

            check_model = Model.session_map.objects.get(url_id = url_id)

            session_id = check_model.customer_info.session_id
            cust_model = Model.customer_info.objects.get(session_id = session_id)
            lookup_model = Model.customer_lookup.objects.filter(customer_info = session_id).last()
            # handling multi user single coupon validity issue
            if cust_model.service_type_id > 20:
                coupon_valid = self.check_coupon_validity(session_id)
                if coupon_valid:
                    json_str['coupon_valid'] = 'true'
                else:
                    json_str['coupon_valid'] = 'false'
            if lookup_model:
                json_str['vendor_name'] = lookup_model.vendor_name
            json_str['customer_type'] = cust_model.customer_type
            # if cust_model.name and cust_model.father_name:
            json_str['name'] = cust_model.name
            json_str['father_name'] = cust_model.father_name
            json_str['id_type'] = cust_model.id_type
            if json_str['id_type'] == '1':
                json_str['id_no'] = cust_model.adhaar_number
                # gender
                json_str['gender'] = cust_model.gender
            else:
                json_str['id_no'] = cust_model.dl_number
            json_str['address'] = cust_model.address
            json_str['dob'] = str(cust_model.dob)
            json_str['customer_type'] = cust_model.customer_type
            json_str['uan'] = cust_model.uan
            if cust_model.service_type_id > 20:
                json_str['coupon'] = '1'
            json_str['service_type_id'] = str(cust_model.service_type_id)
            json_str['language_type'] = cust_model.language_type
            db_time = check_model.updated_at
            # get the time difference
            # import datetime
            db_time = db_time.replace(tzinfo=None)
            now = datetime.now().replace(tzinfo=None)#datetime.datetime.utcnow().replace(tzinfo=utc)
            timediff = now - db_time
            #print'isurlvalid timediff--->',timediff)
            time_diff = timediff.total_seconds()//60
            json_str['url_id'] = url_id
            json_str['is_valid'] = "Success"
            
            service_model = Model.service_detail.objects.filter(customer_type = cust_model.customer_type, service_type_id=cust_model.service_type_id).last()
            check_name = Model.check_types(service_model.check_types).name
            if 'kyc' in check_name:
                json_str['kyc'] = True
            else:
                json_str['kyc'] = False    

            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            json_str = {}
            json_str['is_valid'] = "Fail"
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                # json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # Submit user details 
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def submit_user_detail(self, request):
        password = "qwerty@98765".encode()
        cust_model = ''
        try:
            # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
            #     data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            # else:
            data = request.data
            url_id = data["url_id"]
            json_str = {}
            check_model = Model.session_map.objects.filter(url_id = url_id).last()
            session_id = check_model.customer_info.session_id
            cust_model = Model.customer_info.objects.get(session_id=session_id)
            service_model = Model.service_detail.objects.filter(customer_type = cust_model.customer_type, service_type_id=cust_model.service_type_id).last()
            check_name = Model.check_types(service_model.check_types).name
            if cust_model.id_type == "1":
                cust_model.adhaar_number = data["id_no"]
                # cust_model.gender = data["gender"] #temp check
            else:
                cust_model.dl_number = data["id_no"]
            cust_model.address = data["address"]
            cust_model.dob = data["dob"]
            cust_model.name = data["name"]
            cust_model.father_name = data["father_name"]
            if 'emp' in check_name:
                cust_model.uan = data["uan"]
            if data.get('current_address'):
                kyc_obj = Model.kyc_report_data.objects.filter(customer_info=session_id).last()
                kyc_obj.current_address = data["current_address"]
                kyc_obj.stay_from = data["stay_from"]
                kyc_obj.stay_to = data["stay_to"]
                kyc_obj.ownership_status = data["ownership_status"]
                kyc_obj.save()
            cust_model.save()
            json_str['status'] = 'Success'
            json_str['url_id'] = url_id
            json_str['name'] = cust_model.name
            json_str['father_name'] = cust_model.father_name
            
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_200_OK)
        except Exception as ex:
            json_str = {}
            json_str['status'] = 'Fail'
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->"+"cust_id = "+str(cust_model.session_id))
            logging.exception((inspect.currentframe().f_code.co_name).upper())

            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # Verify mobile otp of customer
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_mobile_otp_frontend(self, request):
        password = "qwerty@98765".encode()
        try:
 
            # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
            #     data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            # else:
            data = request.data            
            jsn_data = {}
            url_id = data["url_id"]
            jsn_data["url_id"] = url_id
            # if data.get('dav'):                
            #     order_obj = Model.order.objects.filter(order_id=url_id).last()
            #     session_id = order_obj.customer_info.session_id
            # else:
            map_model = Model.session_map.objects.filter(url_id=url_id).last()
            session_id = map_model.customer_info.session_id
            otp = data['otp']
            otp_process = check_processors.VerifyMobileOTPProcessor()
            res = otp_process.process(session_id, otp)                        
            if res:
                jsn_data["verification"] = "Success"
            else:
                jsn_data["verification"] = "Fail"
            
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                jsn_data = json.dumps(jsn_data)
                jsn_data = self.encrypt(jsn_data.encode(), password)
            return Response(jsn_data,status = status.HTTP_200_OK)
            
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            jsn_data = {}
            jsn_data["verification"] = "Fail"
            
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                jsn_data = json.dumps(jsn_data)
                jsn_data = self.encrypt(jsn_data.encode(), password)
            return Response(jsn_data, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # save user consent for both myself and someoneelse
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def user_consent(self, request): 
        password = "qwerty@98765".encode()   
        try:
            appbackend = whatsapp_backend_api.Whatsapp_backend()
            # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
            #     data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            # else:
            data = request.data
            url_id = data['url_id']
            session_obj = Model.session_map.objects.filter(url_id = url_id).last()
            session_id = session_obj.customer_info.session_id
            cust_model = session_obj.customer_info
            mobile_no = session_obj.mobile_no
            payload = {'session_id': session_id}
            
            jsn_data={}
            jsn_data["consent"] = "Success"
            jsn_data["customer_type"] = cust_model.customer_type
            update_cantidate_notification_for_strors(session_id,cust_model.customer_type)
            update_cantidate_notification_for_partners(session_id,cust_model.customer_type)
            # delete entry from reminder is candidate cmplete the process
            if cust_model.customer_type == '3' and cust_model.service_type_id:                
                lookup_model = Model.customer_lookup.objects.filter(customer_info = session_id).last()
                order_obj = Model.order.objects.get(customer_info = session_id)

                constent_obj = Model.consent()
                constent_obj.order = order_obj
                constent_obj.name = cust_model.name
                constent_obj.mobile_number = cust_model.mobile_no
                constent_obj.save()
                pay_obj = processor.DB_Processor()
                if cust_model.language_type == 1:
                    question_desc = 'Thank you for your confirmation. We will share the background verification report to *' + (lookup_model.vendor_name).upper() + '*'
                    update_cantidate_notification_for_strors(session_id,cust_model.customer_type)
                    update_cantidate_notification_for_partners(session_id,cust_model.customer_type)
                else:
                    question_desc = 'आपकी पुष्टि के लिए धन्यवाद। हम बैकग्राउंड वेरिफिकेशन रिपोर्ट *' + (lookup_model.vendor_name).upper() + '* को साझा करेंगे'
                pay_obj.sent_reminder(lookup_model.candidate_mobile, question_desc)
                # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                #     if mobile_no not in ['+9181307335051','+9198990117421','+9192052640131']:
                appbackend.set_checks(payload)                         

                Model.reminder.objects.filter(customer_info = session_id).delete()

                # url status in url_expiry model
                url_expire_model = Model.url_expiry.objects.get(url_id = url_id)
                url_expire_model.expired = True
                url_expire_model.save()

            
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                jsn_data = json.dumps(jsn_data)
                jsn_data = self.encrypt(jsn_data.encode(), password)
            return Response(jsn_data,status = status.HTTP_200_OK)

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            jsn_data = {}
            jsn_data["verification"] = "Fail"
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                jsn_data = json.dumps(jsn_data)
                jsn_data = self.encrypt(jsn_data.encode(), password)
            return Response(jsn_data, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # payment details sent to frontend for razorpay hit
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def set_payment_detail(self, request):
        password = "qwerty@98765".encode()
        try:
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            else:
                data = request.data
            url_id = data["url_id"]
            mob_model = Model.session_map.objects.filter(url_id = url_id).last()
            session_id = mob_model.customer_info.session_id
            cust_model = Model.customer_info.objects.get(session_id = session_id)
            # save gst detail in customer session information
            if 'gst_no' in data:
                gst_no = data["gst_no"]
                gst_add = data["gst_add"]

                if gst_no == "":
                    cust_model.customer_gstin = "NA"
                else:
                    cust_model.customer_gstin = gst_no
                if gst_add == "" and cust_model.customer_type == '1' and cust_model.name: 
                    cust_model.customer_gst_address = (cust_model.name).upper()
                else:
                    cust_model.customer_gst_address = gst_add
                cust_model.save()
            # set payment details to send to frontend
            name = cust_model.name
            customer_type = cust_model.customer_type
            service_type_id = cust_model.service_type_id
            service_model = Model.service_detail.objects.filter(customer_type = customer_type,service_type_id = service_type_id).last()
            package_name = service_model.service_type_name
            net_amount = cust_model.final_price
            #making package price rs 1 for testing for particular numbers
            reg_model = Model.customer_register.objects.get(mobile_no = cust_model.mobile_no)
            if reg_model.mobile_verified == True:
                net_amount = 1   

            # kyc_list = [4, 7, 26]
            # if service_type_id in kyc_list:
            #     name = 'NA'
            # else:
            # capitalize name
            name = ' '.join([x.capitalize() for x in name.split()])
            json_str = {}
            json_str["contact"] = (cust_model.mobile_no).replace("+91","")
            json_str["order_id"] = session_id
            json_str["name"] = name
            json_str["amount"] = round(net_amount,2)
            json_str["package_name"] = name #update this on frondend too
            json_str["email"] = "" # new changes
            json_str["description"] = "HV WHATSAPP PAYMENT"
            json_str["url_id"] = url_id
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str,status = status.HTTP_200_OK)
        
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    #backend api object creation

    # get razor details after razorpay hit
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_payment_detail(self, request):
        password = "qwerty@98765".encode()
        try:
            payment_process = check_processors.PaymentProcessor()
            # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
            #     data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            # else:
            data = request.data
            #print"DATA:",data)
            url_id = data["url_id"]
            mob_sess_obj = Model.session_map.objects.filter(url_id = url_id).last()
            session_id = mob_sess_obj.customer_info.session_id
            # check if customer hit with coupon code 
            if "coupon_valid" in data:
                is_coupon = True
            else:
                is_coupon = False

            data["is_coupon"] = is_coupon

            if is_coupon:
                data['txn_id'] = "Coupon Code"
                json_str = {}
                result = 'Success'
                json_str['result'] = result
                # call thread to execute other processes
                t1 = threading.Thread(target=self.after_get_payment, args=(data,))
                t1.start()
            else:
                res = payment_process.afterRazorPayment(data,session_id) 
                if res["status"] == "authorized" or res["status"] == "captured":
                    data['txn_id']= res['txn_id']
                    data["email"] = res["email"]
                    json_str = {}
                    result = 'Success'
                    json_str['result'] = result
                    # call thread to execute other processes
                    t1 = threading.Thread(target=self.after_get_payment, args=(data,))
                    t1.start()
                else:
                    data['txn_id']= res['txn_id']
                    json_str = {}
                    result = 'Fail'
                    json_str['result'] = result
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
                    
                
            return Response(json_str, status = status.HTTP_200_OK)
        except Exception as ex:
            json_str = {}
            result = 'Fail'
            json_str['result'] = result
            json_str = json.dumps(json_str)
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_200_OK)

    def send_demo_report(self, session_id):
        if session_id == 4873:
            try:
                views.generate_report('+919205264013', session_id)
                pay_obj = processor.DB_Processor() 
                url = 'https://checkapi.helloverify.com/media/ihv/Report_E8AA414B.pdf'
                time.sleep(10)

                views.encrypt_report(url, 'saurabh verma', '+919205264013') #temp
                pay_obj.sent_reminder('+919205264013', 'Report', url)
                return ''
            except Exception as ex:
                traceback.print_exc()
                logging.warning("<----------"+str(datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
                return False
        elif session_id == 11640:
            try:
                views.generate_report('+919928927887', session_id)
                pay_obj = processor.DB_Processor() 
                url = 'https://checkapi.helloverify.com/media/ihv/Report_159EF711632.pdf'
                time.sleep(10)

                views.encrypt_report(url, 'saurabh jain', '+919928927887') #temp
                pay_obj.sent_reminder('+919928927887', 'Report', url)
                return ''
            except Exception as ex:
                traceback.print_exc()
                logging.warning("<----------"+str(datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
                return False


    def after_get_payment(self, data):
        from hv_whatsapp_api.signals import aadhaar_automation_seven
        try:
            appbackend = whatsapp_backend_api.Whatsapp_backend()
            url_id = data["url_id"]
            # url status in url_expiry model
            url_expire_model = Model.url_expiry.objects.get(url_id = url_id)
            url_expire_model.expired = True
            url_expire_model.save()
            mob_sess_obj = Model.session_map.objects.filter(url_id = url_id).last()
            session_id = mob_sess_obj.customer_info.session_id    
            mobile_no = mob_sess_obj.mobile_no
            cust_obj = Model.customer_info.objects.get(session_id = session_id)
            cust_obj.payment_status = 1
            cust_obj.save()

            #deleting entry from admin incomplete model
            Model.AdminIncompleteTransactionModel.objects.filter(customer_info = session_id).delete()

            # promocode_obj = Model.PromoCodes.objects.filter(customer_info = session_id).last()
            # if promocode_obj:
            #     promocode_obj.is_redeemed = True
            #     promocode_obj.save()
            is_coupon = data["is_coupon"]
            # Check coupon code status
            if is_coupon:
                payload = {'session_id': session_id, 'txn_id': "Coupon Code"}
                order_id, session_id = appbackend.create_order(payload)
                #redeem coupon once user give consent in coupon code flow
                if not cust_obj.gift_card:
                    code_obj = Model.UniqueCodes.objects.filter(customer_info = payload['session_id']).last()
                    code_obj.is_redeemed = True
                    code_obj.save()
            else:
                payload = {'session_id': session_id, 'txn_id': data["txn_id"]}
                order_id, session_id = appbackend.create_order(payload)
                #customer register - save email id and name
                cust_reg = Model.customer_register.objects.get(mobile_no = mobile_no)
                cust_reg.email_id = data["email"]
                cust_reg.name = cust_obj.name
                cust_reg.save()

            # order_obj = Model.order.objects.filter(session_id = session_id).last()
            if cust_obj.customer_type == '2' or cust_obj.customer_type == '3':
                obj_ques = Model.question_master.objects.get(question_id = 60)
                if cust_obj.language_type == 1:
                    question_desc = obj_ques.question_desc_eng
                elif cust_obj.language_type == 2:
                    question_desc = obj_ques.question_desc_hindi
                lookup_obj = Model.customer_lookup.objects.get(customer_info = session_id)
                question_desc = question_desc.replace('{_order_id_}', str(order_id))
                question_desc = question_desc.replace('{_candidate_}', (lookup_obj.candidate_name).upper())

                pay_obj = pr.DB_Processor()
                pay_obj.sent_reminder(mobile_no, question_desc)
                cand_obj = Model.customer_info.objects.filter(mobile_no = lookup_obj.candidate_mobile).last()
                lookup_payload = {'mobile_no': lookup_obj.candidate_mobile, 'session_id': session_id, 'getpay': 'pay', 'cust_obj': cand_obj}
                appbackend.save_mobile_session(lookup_payload)
                # set reminder entry
                payload = {
                    "session_id":session_id
                }
                pay_obj.save_entry_to_reminder_table(payload)
            else:
                pay_obj = processor.DB_Processor()    
                # if cust_obj.service_type_id != 26: #not the coupon flow
                obj_ques = Model.question_master.objects.get(question_id = 13)
                if cust_obj.language_type == 1:
                    question_desc = obj_ques.question_desc_eng
                elif cust_obj.language_type == 2:
                    question_desc = obj_ques.question_desc_hindi
                question_desc = question_desc.replace('{_order_id_}', str(order_id))
                pay_obj.sent_reminder(mobile_no, question_desc)
            # for invoice
            if is_coupon:
                pass
            else:
                config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
                url = 'https://checkapi.helloverify.com/case/invoice/url_id'
                invoice_name = 'Invoice_' + str(order_id)
                url = url.replace('url_id', invoice_name)
                save_dir = 'static/reports/url_id.pdf'.replace('url_id', invoice_name)
                pdfkit.from_url(url, save_dir, configuration = config)
                url = 'https://checkapi.helloverify.com/static/reports/url_id.pdf'.replace('url_id', invoice_name)
                pay_obj.sent_reminder(mobile_no, invoice_name, url)
                
                #send report automatically for demo
                if cust_obj.adhaar_number == '244340560639' and cust_obj.customer_type == '1':
                    self.send_demo_report(4873)
                if cust_obj.dl_number == 'rj2720090142779'and cust_obj.customer_type == '1':
                    self.send_demo_report(11640)
            if cust_obj.customer_type == '2':
                appbackend.send_message_to_candidate(payload)
            if mob_sess_obj.customer_info.service_type_id in (27,28):    
                aadhaar_automation_seven(session_id)    
            return True
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    
    '''
    call anticaptcha for addhar verification
    '''
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @retry(stop_max_attempt_number=4, wait_random_min=2000, wait_random_max=3000)
    def aadhaar_verification(self, request):
        try:
            try:
                id_type = 'aadhaar'
                chrome_options.add_argument("--headless")
                chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
                uid_no = request.data['uid']
                getcaptcha = GetCaptcha()
                driver = webdriver.Chrome(executable_path="/usr/lib/chromium-browser/chromedriver", options=chrome_options)
                driver.get("https://resident.uidai.gov.in/verify")
                getcaptcha.download_captcha(driver, id_type, uid_no)
                captcha_text = getcaptcha.get_captcha_text(uid_no)
                driver.implicitly_wait(120)
                uid = driver.find_element_by_xpath('//*[@id="uidno"]')
                captcha = driver.find_element_by_xpath('//*[@id="security_code"]')
                uid.send_keys(uid_no)
                captcha.send_keys(captcha_text)
                driver.find_element_by_xpath('//*[@id="submitButton"]').click()
                elements = driver.find_element_by_xpath('//*[@id="maincontent"]/div/div[1]/div[3]')
                txt = elements.text
            except Exception as ex:
                #print'retrying aadhaar')
                raise Exception("Broken aadhaar api")
                traceback.print_exc()
            return Response(txt)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    '''
    call anticaptcha for dl verification
    '''
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @retry(stop_max_attempt_number=4, wait_random_min=2000, wait_random_max=3000)
    def dl_verification(self, request):
        try:
            try:
                id_type = 'dl'
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
                dl_no = request.data['dl_no']
                dob = request.data['dob']
                getcaptcha = GetCaptcha()
                driver = webdriver.Chrome(executable_path="D:\\HV projects\\ABHI_Saurabh\\fintech_backend\\hv_whatsapp_api\\hv_whatsapp_backend\\driver\\chromedriver.exe", options=chrome_options)
                driver.get("https://parivahan.gov.in/rcdlstatus/?pur_cd=101")
                getcaptcha.download_captcha(driver, id_type)
                captcha_text = getcaptcha.get_captcha_text()
                driver.implicitly_wait(20)
                dl_field = driver.find_element_by_xpath('//*[@id="form_rcdl:tf_dlNO"]')
                dob_field = driver.find_element_by_xpath('//*[@id="form_rcdl:tf_dob_input"]')
                # captcha = driver.find_element_by_xpath('//*[@id="form_rcdl:j_idt32:CaptchaID"]')
                captcha = driver.find_element_by_xpath('//*[@id="form_rcdl:j_idt29:CaptchaID"]')
                dl_field.send_keys(dl_no)
                dob_field.send_keys(dob)
                captcha.send_keys(captcha_text)
                # driver.find_element_by_xpath('//*[@id="form_rcdl:j_idt43"]').click()
                driver.find_element_by_xpath('//*[@id="form_rcdl:j_idt39"]').click()
                # elements = driver.find_element_by_xpath('//*[@id="form_rcdl:j_idt115"]/table[1]/tbody')
                elements = driver.find_element_by_xpath('//*[@id="form_rcdl:j_idt114"]/table[1]/tbody')
                txt = (elements.text).lower()
                txt = (re.sub('\n',' ',txt)).lower()
                dl_number = txt[txt.find('dl no.:'):]
                dl_number = re.sub('dl no.: ','',dl_number)
                name = re.search('name:.*date of issue', txt)
                if name:
                    name = (re.sub(r'(name:)|(date of issue)', '', name.group())).strip()
                payload = {'dl_no':dl_number, 'name': name}
                # res = json.dumps(payload)
                res = payload
            except Exception as ex: 
                res = {'dl_no':'na', 'name':''}      
                traceback.print_exc()
                logging.warning("<----------"+str(datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
                raise Exception("Broken DL api")
            return Response(res)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())


    def criminal_check_external_manual_resp(self,order_id,color_code,additional_data):
        external_record = Model.criminal_result_external.objects.filter(order = order_id).last()
        if external_record:
            if color_code.upper() == "RED":
                external_record.manual_color_code = 2 #his is for red, for orange color code is 3  
                external_record.is_check_passed = False
            else:
                external_record.manual_color_code = 1 #this is for green
                external_record.is_check_passed = True

            external_record.final_result_json = additional_data
            external_record.save()
            
            return Response(True, status=status.HTTP_200_OK)
        return Response('Order Id does not exist', status=status.HTTP_400_BAD_REQUEST)
    '''
    store criminal manual response
    '''
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def store_crime_check_response(self, request):    
        try:
            order_id = request.data.get('CheckId','')
            color_code = request.data.get('ColorCode','')
            additional_data = request.data.get('AdditionalData','')

            record = Model.criminal_result.objects.filter(order = order_id).last()

            if record is None:
                self.criminal_check_external_manual_resp(order_id,color_code,additional_data)
                return Response('Order Id does not exist', status=status.HTTP_400_BAD_REQUEST)            
            if color_code.upper() == "RED":
                record.manual_color_code = 2 #his is for red, for orange color code is 3  
                record.is_check_passed = False
                record.ps_color_code = 2
            else:
                record.manual_color_code = 1 #this is for green
                record.is_check_passed = True
                record.ps_color_code = 1

            record.manual_response = additional_data
            record.remark = "Manual response received"
            record.save()
            
            # set crime check flag for scheduler
            report_model  = Model.report_check.objects.get(order = order_id)
            report_model.crime_check_status = True
            report_model.save()

            return Response(True, status=status.HTTP_200_OK)                                
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    '''
    NOT IN USE
    '''
    # @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    # def store_manual_dl_response(self, request):    
    #     try:
    #         checkid = request.data.get('CheckId','')
    #         color_code = request.data.get('ColorCode','')
    #         additional_data = request.data.get('AdditionalData','')

    #         record = Model.check_crime_result.objects.filter(check_id = checkid).last()

    #         if record is None:
    #             return Response('CheckId does not exist', status=status.HTTP_400_BAD_REQUEST)            
    #         if color_code.upper() == "RED":
    #             record.manual_color_code = 2 #his is for red, for orange color code is 3  
    #             record.is_check_passed = False
    #             record.ps_color_code = 2
    #         else:
    #             record.manual_color_code = 1 #this is for green
    #             record.is_check_passed = True
    #             record.ps_color_code = 1
    #         record.manual_response = additional_data
    #         record.remark = "Manual response received"
    #         record.save()
    #         return Response(True, status=status.HTTP_200_OK)                                
    #     except Exception as e:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    '''
    NOT IN USE
    '''
    # @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    # def dl_manual_form(self, request):
    #     try:
    #         form = DLManualEntry(request.POST)

    #         context = {
    #             'form': form,
    #         }
            
    #         template = '..\\templates\\hv_whatsapp_api\\form\\dl_manual_entry.html'
    #         return render(request, template, context)
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    '''
    NOT IN USE
    '''
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def test_razorpay_capture(self, request):
        try:
            data = request.data
            
            amount = data["amount"]
            txn_id = data["txn_id"]
            check_pro = check_processors.PaymentProcessor()
            res = check_pro.capture_payment(data)
            #printres)
            #res = json.loads(res)

            return Response(res, status=status.HTTP_200_OK)     
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    # def set_kyc_report_status(self, request):
    #     try:
    #         data = request.data
    #         report_name = data["report_name"]
    #         order_exp = '[0-9]{8}'
    #         order_id = re.search(order_exp, report_name).group()
    #         kyc_obj = Model.kyc_check.objects.filter(order_id = order_id).last()
    #         if kyc_obj:
    #             kyc_obj.report_name = report_name
    #             kyc_obj.save()
    #             subject = "KYC Report Generated"
    #             content = "KYC Report generated for order_id: "+order_id
    #             mail_process = mail.Send_Email()
    #             mail_process.process(subject,content) 
    #         return Response('Success', status = status.HTTP_200_OK)
    #     except Exception as ex:
    #         print(str(ex))
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"--"+str(ex)+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return Response('Success', status = status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def fetch_all_payment_from_razorpay(self, request):
        try:
            import razorpay
            razorkey = app_settings.RAZORPAY_KEYS['RAZORKEY']
            razorsecret = app_settings.RAZORPAY_KEYS['RAZORSECRET']
            client = razorpay.Client(auth=(razorkey, razorsecret))
            payload = {}
            payload["count"] = 100
            import datetime
            t = datetime.datetime.now()
            sec = int((t-datetime.datetime(1970,1,1)).total_seconds())
            #printsec)
            payload["from"] = sec - 432000
            resp = client.payment.fetch_all(data = payload)
            items = resp["items"]
            #printitems)
            return Response(items, status = status.HTTP_200_OK)
        except Exception as ex:
            #printstr(ex))
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_customer_data(self, request):
        password = "qwerty@98765".encode()        
        try:
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            else:
                data = request.data
            #url_id is equivalent to order_id
            order_id = data["url_id"]
            order_obj = Model.order.objects.get(order_id = order_id)
            session_id  = order_obj.customer_info.session_id

            #fetching detail to decide wheather to show otp and consent page or not
            payload = {}
            payload["coupon"] = (order_obj.customer_info.service_type_id > 20)
            payload["service_type_id"] = order_obj.customer_info.service_type_id
            payload["customer_type"] = order_obj.customer_info.customer_type
            
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                json_str = json.dumps(payload)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_200_OK)
            
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            jsn_data = {}
            jsn_data["verification"] = "Fail"
            
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                jsn_data = json.dumps(jsn_data)
                jsn_data = self.encrypt(jsn_data.encode(), password)
            return Response(jsn_data, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_badge_data(self, request):
        password = "qwerty@98765".encode()        
        try:
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                # data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
                data = request.data #temp
            else:
                data = request.data
          
            payload = Model.report.objects.filter(order = data["order_id"]).last()          
            # payload = Model.report.objects.filter(session_id = '596b42ac8bdd4db4ab29d5b74f5ab0fc').last()          
            # payload = Model.report.objects.filter(session_id = 'a51e3af6984942d9b327281b1033f2c0').last()          
            json_str = json.loads(payload.report_json)
            if 'dl' in json_str.keys():
                json_str["id_type"] = 'driving_licence'
            elif 'adhaar' in json_str.keys():
                json_str["id_type"] = 'adhaar'  
            else:                
                json_str = {'result': 'Invalid order_id'}

            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True: #temp
                json_str = json.dumps(json_str)
                json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_200_OK)
            
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            jsn_data = {}
            jsn_data["status"] = "Fail"
            
            if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True: #temp
                jsn_data = json.dumps(jsn_data)
                jsn_data = self.encrypt(jsn_data.encode(), password)
            return Response(jsn_data, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    # def post_dav_local(self, request):      
    #     try:
    #         digital_url = app_settings.EXTERNAL_API["DIGITAL_ADDRESS1"]
    #         payload = {}
    #         order_id = request.data["order_id"]
    #         now = datetime.now()
    #         payload["DACheckId"] = '{}/{}-ADD-1'.format(order_id, now.year)
    #         payload["CaseId"] = order_id

    #         headers = {'Content-type': 'application/json'}
    #         print(payload)
    #         req = requests.post(digital_url,data=str(payload), headers = headers)

    #         # payload = {}
    #         # payload["DACheckId"] = '98970943/2020-ADD-1'
    #         # payload["CaseId"] = '98970943'
    #         # headers = {'Content-type': 'application/json'}
    #         # requests.post('http://203.52.45.237:8056/DAMaster/postcandidateDetails', data=str(payload), headers = headers)
    #         return Response(json_str, status = status.HTTP_200_OK)
            
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return Response('issue', status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def test_api(self, request):  
        try:
            batch = Model.EducationData.objects.filter(message_sent = False)
            if batch:
                for item in batch:                
                    ques_desc = Model.question_master.objects.get(question_id = 1005)
                    # final_ques_desc = self.update_question(ques_desc.question_desc_eng, 1001, item)                    
                    self.sent_reminder(item.mobile_no, ques_desc)
                batch.update(message_sent = True)
            batch = Model.EducationData.objects.filter(case_status = '0', doc_reminder__gt = 0) #pending
            if batch:
                for item in batch:
                    time_diff = self.find_time_difference_in_minutes(item.updated_at)
                    if time_diff in range(24*60, 24*60+2) or time_diff in range(48*60, 48*60+2) or time_diff in range(72*60, 72*60+2):
                        ques_desc = Model.question_master.objects.get(question_id = 1002)

                        final_ques_desc = self.update_question(ques_desc.question_desc_eng, 1002, item)

                        self.sent_reminder(item.mobile_no, final_ques_desc)
                        item.doc_reminder = item.doc_reminder - 1
                        item.save()
                        return True
            batch = Model.EducationData.objects.filter(Q(case_status = '3') | Q(case_status = '4') | Q(case_status = '5'), insuff_reminder__gt = 0) #insuff
            if batch:
                for item in batch:
                    time_diff = self.find_time_difference_in_minutes(item.updated_at)
                    if time_diff in range(24*60, 24*60+2) or time_diff in range(48*60, 48*60+2) or time_diff in range(72*60, 72*60+2):
                        ques_desc = Model.question_master.objects.get(question_id = 1003)
                        final_ques_desc = self.update_question(ques_desc.question_desc_eng, 1003, item)                    
                        self.sent_reminder(item.mobile_no, final_ques_desc)
                        item.insuff_reminder = item.insuff_reminder - 1
                        item.save()
                        return True
            return True
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)
    
    def update_question(self, ques_desc, ques_id, edu_obj):
        # edu_obj = Model.EducationData.objects.filter()
        try:
            if ques_id == 1001:
                final_ques_desc = ques_desc.replace("{{1}}", edu_obj.unique_id)
                if edu_obj.tenth == 'Yes' and edu_obj.twelveth == 'Yes':
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*10th and 12th*')
                elif edu_obj.twelveth == 'Yes':
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*12th*')
                else:
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*10th*')
                final_ques_desc = final_ques_desc.replace("{{3}}", edu_obj.name)
            elif ques_id == 1002: 
                final_ques_desc = ques_desc.replace("{{1}}", edu_obj.unique_id)
                if edu_obj.case_status == '2':
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*10th*')
                if edu_obj.case_status == '3':
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*12th*')
                if edu_obj.case_status == '4':
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*10th and 12th*')
                final_ques_desc = final_ques_desc.replace("{{3}}", edu_obj.name)
                hours = 72 - ((datetime.now() - edu_obj.created_at).total_seconds())//(60 * 60)
                final_ques_desc = final_ques_desc.replace("{{4}}", hours)
            elif ques_id == 1003:
                final_ques_desc = ques_desc.replace("{{1}}", edu_obj.unique_id)
                if edu_obj.insuff_10th_remark:
                    final_ques_desc = final_ques_desc.replace("{{2}}", edu_obj.insuff_10th_remark)
                elif edu_obj.insuff_12th_remark:
                    final_ques_desc = final_ques_desc.replace("{{2}}", edu_obj.insuff_12th_remark)
                final_ques_desc = final_ques_desc.replace("{{3}}", edu_obj.name)
                hours = str(72 - ((datetime.now() - edu_obj.created_at).total_seconds())//(60 * 60))
                final_ques_desc = final_ques_desc.replace("{{4}}", hours)
            return final_ques_desc
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    def find_time_difference_in_minutes(self, db_time):
        try:
            db_time = db_time.replace(tzinfo=None)
            now = datetime.datetime.now().replace(tzinfo=None)
            timediff = now - db_time
            td = timediff.total_seconds()//60
            return int(td)
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)
    # Send reminder to particular whatsapp number
    def sent_reminder(self,mobile, mesg, url=None):
        try:
            from twilio.rest import Client
            account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
            auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
            client = Client(account_sid, auth_token)
 
            message = client.messages \
                .create(
                    from_='whatsapp:+14157924931',
                    body=mesg,
                    to='whatsapp:'+mobile
                )
            return ''
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # Send reminder to new whatsapp number
    def send_msg_helloverify(self,mobile, mesg, url=None):
        try:
            from twilio.rest import Client
            account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
            auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
            client = Client(account_sid, auth_token)
 
            message = client.messages \
                .create(
                    from_='whatsapp:+14153389961',
                    body=mesg,
                    to='whatsapp:'+mobile
                )
            return ''
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_message_status(self, request):
        try:            
            last_message_sid = request.data.get('MessageSid', None)
            msg_status = request.data.get('MessageStatus', None)
            edu_obj = Model.EducationData.objects.filter(last_message_sid = last_message_sid).last()
            
            
            if edu_obj:
                edu_obj.msg_status = msg_status.upper()
                edu_obj.save()
                
            from promotional_marketing.models import PromotionalMessageTracker
            promo_obj = PromotionalMessageTracker.objects.filter(message_sid = last_message_sid).last()
            if promo_obj:
                promo_obj.msg_status = msg_status.upper()
                promo_obj.save()

            return Response(json.dumps({'result':'success'}), status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_lat_long(self, request):
        try:            
            lat_long = request.data.get('lat_long', None)
            
            lat_long_obj = Model.LatLong.objects.create(lat_long = lat_long)
            
            return Response({'result':'success'}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def initiate_cowin_check(self, request):
        try:            
            check_id = request.data.get('check_id')
            whatsapp_mobile_no = request.data.get('whatsapp_mobile_no')
            name = request.data.get('name')
            email_id = request.data.get('email_id', None)
            birth_year = request.data.get('birth_year', None)
            client_name = request.data.get('client_name', None)
            try:
                Model.CowinData.objects.create(
                    check_id = check_id, 
                    whatsapp_mobile_no = whatsapp_mobile_no,
                    name = name,
                    email_id = email_id,
                    birth_year = birth_year,
                    client_name = client_name)
            except:
                return Response({'result':'Duplicate check id found'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({'result':'success'}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def drug_mesg(self, request):
        try:            
            data = request.data
            mobile_no = data['mobile_no']
            mesg = data['mesg']
            self.send_msg_helloverify(mobile_no, mesg)
            return Response({'result':'success'}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    #API to update asian paint cases status from oniverify
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def edu_status_update(self, request):
        try:            
            case_id = request.data.get('case_id')
            oni_status = request.data.get('oni_status')
            remark = None
            if oni_status == 'insuff':
                remark = request.data.get('remark')
            edu_obj = Model.EducationData.objects.get(case_id = case_id)
            edu_obj.case_status, = self.map_oni_case_status(edu_obj, oni_status, remark)
            edu_obj.save()
            return Response({'result':'success'}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    def map_oni_case_status(self, edu_obj, case_status, remark = None):
        if remark and case_status == '10th':
            edu_obj.insuff_10th_remark = remark
            edu_obj.case_status = case_status
        if remark and case_status == '12th':
            edu_obj.insuff_12th_remark = remark
            edu_obj.case_status = case_status
        if case_status == '1':
            return '0' #inprogress
        if case_status == '1':
            return '0' #inprogress

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def get_redemption_pin(self, request):
        try:            
            product_id = request.data.get('product_id')
            transaction_id = request.data.get('transaction_id')
            my_dict = {
                '888501310868': 21, 
                '888501310869': 22, 
                '888501310870': 23, 
                '888501310871': 24, 
                '888501310872': 25, 
                '888501310873': 26
                }
            service_type_id = my_dict[product_id]

            code_obj = Model.UniqueCodes.objects.filter(service_type_id = service_type_id, is_distributed = False).first()
            code_obj.is_distributed = True
            code_obj.transaction_id = transaction_id
            code_obj.save()
            return Response({'result':'success', 'redemption_pin': 'TEST123'}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def otp_contact(self, request):
        try:
            req = json.dumps(request.data)            
            Model.LatLong.objects.create(lat_long=req)
            return Response({'result':'Success'}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result':'Fail'}, status = status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def razorpay_callback_url(self, request):
        try:
            if request.query_params['razorpay_payment_link_status'] == 'paid':
                callback_t1 = threading.Thread(target=self.send_payment_confirmation_mail, args=(request.query_params['razorpay_payment_link_id'], ))
                callback_t1.start()
                return render(request, 'hv_whatsapp_api/payment_success.html', {})
            return HttpResponse('Payment Failed!!! Try Again.')
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return HttpResponse('Something went wrong.')

    def send_payment_confirmation_mail(self, payment_link_id):
        try:
            mail_obj = send_mail.Send_Email()
            subject = "Payment Success"
            content = "Payment completed successfully!!! - " + payment_link_id
            mail_obj.process(subject, content)
            return True
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result':'Fail'}, status = status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def razorpay_payment_detail(self, request):
        try:
            data = request.data
            try:
                short_url = data["payload"]["payment_link"]["entity"]["short_url"]
                verify_now_obj = Model.VerifyNow.objects.get(short_url=short_url)
                verify_now_obj.transaction_detail = json.dumps(data)
                verify_now_obj.transaction_id = data["payload"]["payment"]["entity"]["id"]
            except Exception as ex:
                return Response({'result':'Success'}, status = status.HTTP_200_OK)
            verify_now_obj.email = data["payload"]["payment"]["entity"]["email"]
            verify_now_obj.transaction_captured = data["payload"]["payment"]["entity"]["captured"]
            verify_now_obj.razorpay_payment_link_status = data["payload"]["order"]["entity"]["status"]
            verify_now_obj.discount = verify_now_obj.service_detail.service_type_price -\
                data["payload"]["order"]["entity"]["amount_paid"]/100
            verify_now_obj.is_redemption_pin_shared = True
            t1 = threading.Thread(target=self.send_invoice, args=(verify_now_obj, ))
            t1.start()
            t2 = threading.Thread(target=self.send_redemption_pin, args=(verify_now_obj.id, ))
            t2.start()
            return Response({'result':'Success'}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result':'Success'}, status = status.HTTP_200_OK)

    def send_redemption_pin(self, id):
        try:
            time.sleep(10)
            verify_now_obj = Model.VerifyNow.objects.get(pk=id)
            unique_obj = Model.UniqueCodes.objects.filter(service_type_id=verify_now_obj.service_type_id,\
                is_distributed=False, is_redeemed=False).exclude(assigned_to="PayTM").first()
            # if verify_now_obj.mobile_no != "+919205264013":
            unique_obj.is_distributed = True
            unique_obj.assigned_to = 'Verify Now - ' + verify_now_obj.mobile_no
            unique_obj.transaction_id = verify_now_obj.transaction_id
            unique_obj.save()
            verify_now_obj.redemption_pin = unique_obj.code
            verify_now_obj.is_active = False
            verify_now_obj.save()
            #share redemption pin with customer
            # msg = Model.question_master.objects.get(question_id=3002).question_desc_eng
            msg = cache.get('verifynow_3002')
            msg = msg.format(code=unique_obj.code)        
            p_obj = processor.DB_Processor()
            p_obj.sent_reminder(verify_now_obj.mobile_no, msg)
            p_obj.sent_reminder(verify_now_obj.mobile_no, unique_obj.code)
            
            #send email for payment confirmation
            if verify_now_obj.mobile_no not in ['+919205264013','+919811374026','+917532973604','+919928927887','+918077344267']:
                mail_obj = send_mail.Send_Email()
                subject = "Received Payment from HelloV"
                service_type_name = verify_now_obj.service_detail.service_type_name.split(' - ')[0]
                amount_received = verify_now_obj.service_detail.service_type_price - verify_now_obj.discount
                if int(amount_received)<10:
                    from twilio.rest import Client
                    msg = f"""Dear HelloV Team,

Package Name - {service_type_name}
Amount received - {amount_received}
Customer Mobile Number - {verify_now_obj.mobile_no}
Customer Email ID - {verify_now_obj.email}"""
                    account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
                    auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
                    client = Client(account_sid, auth_token)
                    client.messages.create(
                        from_='whatsapp:+14157924931',
                        body=msg,
                        to='whatsapp:+917532973604'
                    )
                    client.messages.create(
                        from_='whatsapp:+14157924931',
                        body=msg,
                        to='whatsapp:+919811374026'
                    )
                else:
                    content = f"Package Name - <b>{service_type_name}</b><br>Amount received - <b>₹{amount_received}</b><br>Customer Mobile Number - <b>{verify_now_obj.mobile_no}</b> <br> Customer Email ID - <b>{verify_now_obj.email}</b>"
                    mail_obj.process(subject, content)

            return True
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result':'Fail'}, status = status.HTTP_400_BAD_REQUEST)

    # call invoice json and generate invoice and sent to customer
    def send_invoice(self, verify_now_obj):
        try:
            invoice_dict = {}
            invoice_dict["client_address"] = verify_now_obj.mobile_no[3:]
            invoice_dict["gstin"] = ""
            invoice_dict["date"] = datetime.now().strftime('%d-%m-%Y')
            invoice_dict["gst_no"] = '09AAECH4671D1ZM'
            invoice_dict["pan_no"] = 'AAECH5671D'
            invoice_dict["sac"] = '998521'
            invoice_dict["package_name"] = verify_now_obj.service_detail.service_type_name
            invoice_dict["number_of_case"] = '1'
            invoice_dict["amount"] = verify_now_obj.service_detail.service_type_price
            invoice_dict["total_amount"] = verify_now_obj.service_detail.service_type_price
            discount = verify_now_obj.service_detail.service_type_price - verify_now_obj.discount
            invoice_dict["discount"] = discount
            invoice_dict["net_amount"] = verify_now_obj.service_detail.service_type_price - verify_now_obj.discount
            verify_now_obj.invoice_json = json.dumps(invoice_dict)
            verify_now_obj.save()

            #generate and send invoice
            config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")
            url = 'https://checkapi.helloverify.com/case/verify_now_invoice/url_id'
            invoice_name = 'Invoice_' + str(verify_now_obj.id) + str(verify_now_obj.mobile_no[3:8])
            url = url.replace('url_id', str(verify_now_obj.id))
            save_dir = 'static/reports/url_id.pdf'.replace('url_id', invoice_name)
            pdfkit.from_url(url, save_dir, configuration = config)
            url = 'https://checkapi.helloverify.com/static/reports/url_id.pdf'.replace('url_id', invoice_name)
            
            pay_obj = processor.DB_Processor()
            pay_obj.sent_reminder(verify_now_obj.mobile_no, invoice_name, url)
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_lat_long(self, request):
        try:
            from hv_whatsapp_api.hv_whatsapp_frontend import views
            claimed_address = request.data.get('claimed_address')
            actual_lat_long = request.data.get('actual_lat_long')
            request_id = request.data.get('request_id')
            browser_name = request.data.get('browser_name')
            operating_system = request.data.get('operating_system')
            browser_version = request.data.get('browser_version')
            mobile_no = request.data.get('mobile_no')
            candidate_name = request.data.get('candidate_name')
            nearest_landmark = request.data.get('nearest_landmark', '')
            if len(nearest_landmark) > 2 and 'not ' not in nearest_landmark.lower():
                nearest_landmark = request.data.get('nearest_landmark', '')
            else:
                nearest_landmark = ''
            claimed_lat_long, res_data = views.get_lat_long(claimed_address, nearest_landmark)
            final_claimed_lat_long, actual_lat_long, min_distance, location_match = views.find_location_match(claimed_lat_long, actual_lat_long)
            lat_long_payload = {
                'claimed_lat_long': final_claimed_lat_long,
                'actual_lat_long': actual_lat_long,
                'location_match': location_match,
                'distance': min_distance}
            lat_long_obj = Model.LatLong()
            lat_long_obj.claimed_lat_long = final_claimed_lat_long
            lat_long_obj.claimed_address = claimed_address
            lat_long_obj.request_id = request_id
            lat_long_obj.location_json = res_data
            lat_long_obj.actual_lat_long = actual_lat_long
            lat_long_obj.is_match = location_match
            lat_long_obj.distance = min_distance
            lat_long_obj.browser_name = browser_name
            lat_long_obj.operating_system = operating_system
            lat_long_obj.browser_version = browser_version
            lat_long_obj.nearest_landmark = nearest_landmark
            lat_long_obj.mobile_no = mobile_no
            lat_long_obj.candidate_name = candidate_name
            lat_long_obj.save() 
            return Response(lat_long_payload, status = status.HTTP_200_OK)
        except Exception as ex:
            # traceback.print_exc()
            # logging.warning("<----------"+str(datetime.now())+"---------->")
            # logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result':'Fail'}, status = status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def save_bank_name(self, request):
        try:
            data = request.data
            bank_name = data.get('bank_name', None)
            request_id = data.get('request_id', None)
            Model.VisaBankDetail.objects.create(bank_name = bank_name, request_id=request_id)
            return Response({'data': 'success'}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result':'Fail'}, status = status.HTTP_400_BAD_REQUEST)
        
     # Save selfie, Signature and Location for SSL checks
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def save_ssl_data(self, request):
        from hv_whatsapp_api.hv_whatsapp_backend.serializers import SSLCheckSerializer
        password = "qwerty@98765".encode()
        try:
            # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
            #     data = json.loads(self.decrypt(request.data["encryptedPayload"], password).decode("utf-8"))
            # else:
            data = request.data
            
            json_str = {}
            url_id = data["url_id"]
            session_map_obj = Model.session_map.objects.filter(url_id=url_id).last()
            cust_obj = session_map_obj.customer_info
            if cust_obj:                    
                data['customer_info'] = cust_obj.pk
                serializer = SSLCheckSerializer(data=data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    json_str['url_id'] = url_id
                    json_str["data_store"] = "Success"          
                    # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
                    #     json_str = json.dumps(json_str)
                    #     json_str = self.encrypt(json_str.encode(), password)
                    return Response(json_str, status = status.HTTP_200_OK)            
        except Exception as ex:            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            json_str = {}
            json_str["data_store"] = "Fail"
            # if app_settings.LOCAL_ENV == False and app_settings.EN_ENCRYPT == True:
            #     json_str = self.encrypt(json_str.encode(), password)
            return Response(json_str, status = status.HTTP_500_INTERNAL_SERVER_ERROR) 
    
    
    # Check service type for SSL checks
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_sercive_type(self, request):
        try:            
            url_id = request.data.get('url_id')
            session_map_obj = Model.session_map.objects.filter(url_id = url_id).last()
            if session_map_obj and session_map_obj.service_type_id == 29:
                return Response({'result':'success', 'status': True}, status = status.HTTP_200_OK)
            else:
                return Response({'result':'success', 'status': False}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR) 
        
        
    # Test API for generate report
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def test_generate_report(self, request):
        from hv_whatsapp_api.views import generate_report
        try:            
           res = generate_report("+919411287010", request.data.get("sid"))
           return Response({'result':'success', 'status': True}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR) 
    
    # Create unique_codes from manual
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def test_generate_unique_codes(self, request):
        from hv_whatsapp_api.views import generate_unique_codes
        from hv_whatsapp_api.hv_whatsapp_backend import whatsapp_backend_api, processor
        from hv_whatsapp_api.models import question_master
        try:
            # nanny_symbol = "👩‍👧‍👦"
            # car_symbol = "🚗"
            # house_symbol = "🏠"
            # msg = question_master.objects.filter(question_id=1112).last()
            # msg = msg.question_desc_eng.format(service="verify")
            # final_msg = msg + nanny_symbol+car_symbol+house_symbol
            sound_symbol = "🔊"
            # ques_desc = Model.question_master.objects.get(question_id = 308)
            # ques_desc = Model.question_master.objects.get(question_id = 1111)
            # final_msg = ques_desc.question_desc_eng.format(sound1=sound_symbol,sound2=sound_symbol)
            # final_msg = 'https://hellov.in/app/'+'87BBF212077'
            
            # send_msg = processor.DB_Processor()
            # send_msg.sent_reminder('+919411287010', final_msg)
            service_id = request.data.get("service_id")       
            rang = request.data.get("rang")        
            res = generate_unique_codes(request,rang,service_id)
            return Response({'result':'success', 'status': True}, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response(ex, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def defaulttest_api(self, request):
        from hv_whatsapp_api.models import question_master
        # from datetime import datetime, timedelta
        # current_datetime = datetime.now()
        # last_31_min_datetime = current_datetime - timedelta(minutes=31)
        # verifynow_queryset = Model.VerifyNow.objects.filter(promo_code__isnull=False,transaction_captured=False,promo_code_used=True,updated_at__lt = last_31_min_datetime)
        # print(verifynow_queryset.query)
        # if len(verifynow_queryset)>0:
        #     for obj in verifynow_queryset:
        #         cust_promo_obj = Model.customer_promocode.objects.filter(promo_code=obj.promo_code.code,mobile_no=obj.mobile_no).last()
        #         cust_promo_obj.allowed_attempt = cust_promo_obj.allowed_attempt + 1
        #         cust_promo_obj.save()
        #     return Response({'result':'success', 'status': True}, status = status.HTTP_200_OK)
        # from hv_whatsapp_api.signals import aadhaar_automation_seven
        # aadhaar_automation_seven('12290')
        # from hv_whatsapp_api.hv_whatsapp_backend.schedulers import generate_report_scheduler,id_check_scheduler1
        # generate_report_scheduler.do(self)
        from hv_whatsapp_api.hv_whatsapp_backend import whatsapp_backend_api, processor
        msg = question_master.objects.filter(question_id=3002).last()
        msg = msg.question_desc_eng.format(code="ZW5C77X246")
        send_msg = processor.DB_Processor()
        
        send_msg.sent_reminder("+919910198204", msg)
        return Response({'result':'Not data found', 'status': True}, status = status.HTTP_200_OK)
        # from datetime import datetime
        # today = datetime.now()
        
        # promocode_queryset = Model.GeneralPromoCodes.objects.filter(is_expired=False)
        # if len(promocode_queryset)>0:
        #     for obj in promocode_queryset:
        #         # specific_date_obj = datetime.strptime(obj.created_at, '%Y-%m-%d')
        #         difference = today - obj.created_at
        #         if obj.expiry_days >= difference.days:
        #             obj.is_expired = True
        #             obj.save()
        #         else:
        #             pass    
        #     return Response({'result':'success', 'status': True}, status = status.HTTP_200_OK)
        # return Response({'result':'Not data found', 'status': True}, status = status.HTTP_200_OK)             
              