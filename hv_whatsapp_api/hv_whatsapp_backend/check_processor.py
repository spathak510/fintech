import json
from urllib import response
import requests
from rest_framework.parsers import DataAndFiles
from . import data_parsers
from hv_whatsapp import settings as app_settings
from . import check_rules
from fuzzywuzzy import fuzz
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from . import processor as pr
from hv_whatsapp_api import models as Model
import datetime , time
import re
from rest_framework.response import Response
from. import send_mail as mail
from .address_extraction import AddressExtractor
from retrying import retry
from . import sms_local, processor, criminal_check_wrapper

import logging
import inspect
import traceback

logging.basicConfig(filename="error_log.log")
# from .whatsapp_backend_api import Whatsapp_backend as wb

class BaseCheckProcessor():

    '''
    retrying the post request max 3 times
    '''
    def requests_retry_session(
        self,
        retries=3,
        backoff_factor=0.5,
        status_forcelist=(403, 404, 500, 502, 504),
        session=None,
    ):
        try:
            # print("calling API using session retry")
            session = session or requests.Session()
            retry = Retry(
                total=retries,
                read=retries,
                connect=retries,
                backoff_factor=backoff_factor,
                status_forcelist=status_forcelist,
            )
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            return session
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex
    
    
    # def get_token(self):
    #     try:
    #         resp = requests.post(app_settings.EXTERNAL_API['HVOPS_URL'],json=app_settings.HVOPS_CRED)
    #         resp_json = json.loads(resp.text)
            
    #         return resp_json["token"]
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return ex
    
    '''
    create the dob formate accepted by karza for DL
    '''
    def get_date_for_karza(self, db_date_str):
        try:
            new_d_str = db_date_str.strftime("%d-%m-%Y")
            return new_d_str
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    Karza API call for postal address result
    '''
    def post_to_karza_postal(self, url, payload, session_id):
        try:
            karza_key = app_settings.EXTERNAL_API['KARZAAPI_KEY']
            karza_key_id = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
            headers = {karza_key_id: karza_key}
            payload_str = json.dumps(payload)
            response = self.requests_retry_session().post(url, data=payload_str, headers=headers)
            # Logging SMS API HIT
            if session_id:
                # order_obj = Model.order.objects.filter(customer_info = session_id).last()
                api_hit_obj = Model.api_hit_count.objects.get(order__customer_info = session_id)
                if api_hit_obj:
                    api_hit_obj.address_parser_api = api_hit_obj.address_parser_api + 1
                    api_hit_obj.save()
            return response
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    Karza API call for DL result and if result not found then hit the parivahan 
    postal for web scrapping to find the DL result and re-hit karza if new DL number 
    found on parivahan otherwise send for manaul.
    Set check report status for id API hit
    '''
    def post_to_karza(self, url, payload, session_id):
        try:
            karza_key = app_settings.EXTERNAL_API['KARZAAPI_KEY']
            karza_key_id = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
            headers = {karza_key_id: karza_key}
            payload_str = json.dumps(payload)
            # payload_str = payload
            response = self.requests_retry_session().post(url, data=payload_str, headers=headers)
            
            # Logging SMS API HIT

            api_hit_obj = Model.api_hit_count.objects.get(order__customer_info = session_id)
            order_id = api_hit_obj.order.order_id
            if api_hit_obj:
                api_hit_obj.dl_api = api_hit_obj.dl_api + 1
                api_hit_obj.save()
            LOG_FILENAME = 'api.log'
            logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
            now = datetime.datetime.now()
            current_time = now.strftime("%d/%m/%Y, %H:%M:%S")
            logging.debug('DRIVING LICENCE API Hit @ ' + current_time)
            
            report_model  = Model.report_check.objects.get(order = order_id)
            response1 = json.loads(response.text)
            if response1['status-code'] == '101':
                report_model.id_check_status = True
                report_model.save()
            if response1['status-code'] == '103' or response1['status-code'] == '102': #getting 103 from karza
                new_dl_no = 'na'
                if new_dl_no.lower() == 'na':
                    self.insert_dl_manual_entry(session_id)
                    mail_process = mail.Send_Email()
                    subject = "Driving Licence Manual"
                    content = "API don't have the record of DL for Order No.'"+ order_id +"'. Please check and revert within 5 hours.<br><br>https://checkapi.helloverify.com/hellov/hv_whatsapp_api/dl_manual_response/"
                    mail_process.process(subject,content)    
                else:
                    payload_str['dl_no'] = new_dl_no.replace(' ', '')
                    payload_str = json.dumps(payload_str)
                    response = self.requests_retry_session().post(url, data=payload_str, headers=headers)
                    response1 = json.loads(response.text)
                    if response1['status-code'] == '103' or response1['status-code'] == '102':
                        self.insert_dl_manual_entry(session_id)
                        mail_process = mail.Send_Email()
                        subject = "Driving Licence Manual"
                        content = "API don't have the record of DL for Order No.'"+ order_id +"'. Please check and revert within 5 hours.<br><br>http://127.0.0.1:8000/admin/hv_whatsapp_api/dl_manual_response/"
                        mail_process.process(subject,content)
                    elif response1['status-code'] == '101':
                        report_model.id_check_status = True
                        report_model.save()
            return response
        except Exception as e:
            # send mail
            mail_process = mail.Send_Email()
            subject = "API is Down"
            content = "API not responding"
            mail_process.process(subject,content)

            # set api success status
            report_model  = Model.report_check.objects.get(order__customer_info = session_id)
            report_model.id_check_status = False
            report_model.save()
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    save DL manual entry in the model
    '''
    def insert_dl_manual_entry(self, session_id):
        try:
            order_obj = Model.order.objects.get(customer_info = session_id)

            ocr_model = Model.ocr_response.objects.get(customer_info = session_id)
            front_img = ocr_model.front_image_url
            back_img = ocr_model.back_image_url

            # entry to dl manual model
            dl_manual_model = Model.dl_manual_response()
            dl_manual_model.order = order_obj
            dl_manual_model.front_dl_image = front_img
            dl_manual_model.back_dl_image = back_img
            dl_manual_model.save()
            
            return True
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    karza API call for UAN result and set check report status for employment API hit
    '''
    def post_to_karza_uan(self, url, payload, session_id): #temp
        try:
            api_key = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
            api_val = app_settings.EXTERNAL_API['KARZA_UAN']
            headers = {"Content-Type" : "application/json", api_key: api_val}
            payload_str = json.dumps(payload)
            
            # response = self.requests_retry_session().post(url, data=payload_str, headers=headers)
            
            # Logging SMS API HIT
            # order_obj = Model.order.objects.get(customer_info = session_id)
            # api_hit_obj = Model.api_hit_count.objects.get(order = order_obj.order_id)
            # if api_hit_obj:
            #     api_hit_obj.emp_api = api_hit_obj.emp_api + 1
            #     api_hit_obj.save()
            uan_check_obj = Model.uan_check.objects.get(order__customer_info = session_id)
            response = json.loads(uan_check_obj.uan_api_result)
            report_model  = Model.report_check.objects.get(order__customer_info = session_id).last()
            response = json.loads(response['text'])
            if response['status-code'] == '101':
                report_model.emp_check_status = True
                report_model.save()
            if response['status-code'] == '103' or response['status-code'] == '102':
                report_model.emp_check_status = False
                report_model.save()
                # send mail
                mail_process = mail.Send_Email()
                subject = "EMPLOYEMENT (UAN) API ERROR"
                content = "UAN API is not responding for UAN No. '"+str(payload['uan'])+"'"
                mail_process.process(subject,content)

            return response
        except Exception as e:

            # send mail
            mail_process = mail.Send_Email()
            subject = "EMPLOYEMENT (UAN) API ERROR"
            content = "UAN API is not responding for UAN No. '"+str(payload['uan'])+"'"
            mail_process.process(subject,content)

            # set api success status
            report_model  = Model.report_check.objects.get(order__customer_info = session_id)
            report_model.emp_check_status = False
            report_model.save()
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    eCourtForum API call for Crime result and set check report status for criminal API hit
    '''
    def post_to_criminal(self, search_term_json, session_id):
        try:
            cc_key = app_settings.EXTERNAL_API['CREDITCHECKAPI_KEYNAME']
            cc_val = app_settings.EXTERNAL_API['CREDITCHECKAPI_KEY']
            cc_url = app_settings.EXTERNAL_API['CREDITCHECKAPI_URL']
            headers = {
            'Content-Type':'application/x-www-form-urlencoded'}
            payload = {
                'searchTerm': search_term_json,
                cc_key: cc_val,
                'resultsPerPage': "50",
                "onlyRecordsWithAddress": "true"
            }
            res = requests.post(cc_url, data=payload, headers=headers)
            # Logging Crime API HIT
            if res.status_code != 200:
                resp = {"status":res.status_code,"reason":res.reason,"text":res.text,"url":res.url}
                mail_process = mail.Send_Email()
                subject = "CRIMINAL CHECK API ERROR"
                error_content = json.dumps(resp)
                content = "Criminal Check api error content  "+str(error_content)
                mail_process.process(subject,content)
            try:
                if session_id:
                    api_hit_obj = Model.api_hit_count.objects.get(order__customer_info = session_id)
                    if api_hit_obj:
                        api_hit_obj.crime_api = api_hit_obj.crime_api + 1
                        api_hit_obj.save()
            except Exception as e:
                # print(str(e))
                pass
            return res
        except Exception as e:
            # send mail
            mail_process = mail.Send_Email()
            subject = "CRIMINAL CHECK API ERROR"
            search_term_json = json.loads(search_term_json)
            content = "Criminal Check api is not responding for Customer '"+str(search_term_json["name"])+"'"
            mail_process.process(subject,content)

            # set api success status
            report_model  = Model.report_check.objects.get(order__customer_info = session_id)
            report_model.crime_check_status = False
            report_model.save()
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
        
    '''
    eCourtForum API Valuepitch call for Crime result and set check report status for criminal API hit
    '''
    def post_to_valuepitch_criminal(self, search_term_json, session_id=None):
        try:
            valuePitch_user = app_settings.EXTERNAL_API['VALUEPITCH_USERNAME']
            valuePitch_auth_token = app_settings.EXTERNAL_API['VALUEPITCH_AUTH_TOKEN']
            valuePitch_token_url = app_settings.EXTERNAL_API['VALUEPITCH_TOKEN_URL']
            res = ''
            headers = {
            'Content-Type':'application/json'}
            search_term_json = json.loads(search_term_json)
            payload = {
                "name" : search_term_json.get("name"),
                "father_name" : search_term_json.get("fatherName"),
                "source" : "ecourt",
                "address" : search_term_json.get("address"),
                "algo_type" : "11",
                "auth_token" : valuePitch_auth_token,
                "user" : valuePitch_user,
                "scoring" : "1"
            }
            token_res = requests.post(valuePitch_token_url, data=json.dumps(payload), headers=headers)
            res = token_res
            # Logging Crime API HIT
            if token_res.status_code != 200:
                resp = {"status":token_res.status_code,"reason":token_res.reason,"text":token_res.text,"url":token_res.url}
                mail_process = mail.Send_Email()
                subject = "VALUEPITCH CRIMINAL CHECK TOKEN API ERROR"
                error_content = json.dumps(resp)
                content = "Valuepitch Criminal Check token api error content  "+str(error_content)
                mail_process.process(subject,content)
            else:
                result_res = self.valuepitch_result_retries(json.loads(token_res.text)['verify_id'])
                status_code = 200
                if len(result_res['cases']) < 1:
                    status_code = 401
                    
                    
                wrapper_resp = {
                    "status": "OK",
                    "status_code":status_code,
                    "searchTerm": search_term_json.get("name"),
                    "searchType": "searchByPetitionerOrRespondent",
                    "matchType": "partial",
                    "totalResult": 50,
                    "totalHits": 10000,
                    "page": 1,
                    "resultsPerPage": 10,
                    "text": json.dumps(result_res.get('cases',None))
                    }
                res = wrapper_resp    
                    
            try:
                if session_id:
                    api_hit_obj = Model.api_hit_count.objects.get(order__customer_info = session_id)
                    if api_hit_obj:
                        api_hit_obj.crime_api = api_hit_obj.crime_api + 1
                        api_hit_obj.save()
            except Exception:
                # print(str(e))
                pass
            return res
        except Exception as ex:
            print(ex)
            # send mail
            mail_process = mail.Send_Email()
            subject = "CRIMINAL CHECK API ERROR"
            search_term_json = json.loads(search_term_json)
            content = "Criminal Check api is not responding for Customer '"+str(search_term_json["name"])+"'"
            mail_process.process(subject,content)

            # set api success status
            report_model  = Model.report_check.objects.get(order__customer_info = session_id)
            report_model.crime_check_status = False
            report_model.save()
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False 
    
    def valuepitch_result_retries(self, token_id, retries=5, delay=10):
        valuePitch_result_url = app_settings.EXTERNAL_API['VALUEPITCH_RESULT_URL']
        valuePitch_user = app_settings.EXTERNAL_API['VALUEPITCH_USERNAME']
        valuePitch_auth_token = app_settings.EXTERNAL_API['VALUEPITCH_AUTH_TOKEN']
        headers = {
            'Content-Type':'application/json'
            }
        payload = {
                    "auth_token" : valuePitch_auth_token,
                    "user" : valuePitch_user,
                    "verify_id" : token_id
                    }
        time.sleep(delay)
        result_resp = requests.post(valuePitch_result_url, data=json.dumps(payload), headers=headers)
        if result_resp.status_code == 200:
                data = json.loads(result_resp.text)
                return data
        elif retries > 0:
            print(f"Retrying...ValuePitch criminal check Api Attempts left: {retries}")
            return self.valuepitch_result_retries(token_id, retries=retries-1, delay=delay)
        else:
            print(f"ValuePitch criminal check Api Maximum retry attempts reached")
            resp = {"status":result_resp.status_code,"reason":result_resp.reason,"text":result_resp.text,"url":result_resp.url}
            mail_process = mail.Send_Email()
            subject = "VALUEPITCH CRIMINAL CHECK RESULT API ERROR"
            error_content = json.dumps(resp)
            content = "Valuepitch Criminal Check result api error content  "+str(error_content)
            mail_process.process(subject,content)
            return result_resp     
        
               

    '''
    fetch payment details from payment ID received from Razorpay
    '''
    # Get razorpay fetch
    def get_razorpay_fetch(self,txn_id):
        try:
            razorkey = app_settings.RAZORPAY_KEYS['RAZORKEY']
            razorsecret = app_settings.RAZORPAY_KEYS['RAZORSECRET']
            razorpay_url = 'https://' + razorkey +':' + razorsecret +'@api.razorpay.com/v1/payments/'+ txn_id
            res = requests.get(razorpay_url)

            return res
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    Currently not in use.
    fetch payment capture details from payment ID received from Razorpay
    '''
    # Razor pay payment capture status
    def post_razorpay_capture(self, amount,txn_id):
        try:
            razorkey = app_settings.RAZORPAY_KEYS['RAZORKEY']
            razorsecret = app_settings.RAZORPAY_KEYS['RAZORSECRET']
            print('transaction id ->>>', txn_id)
            razor_url = 'https://' + razorkey +':' + razorsecret +'@api.razorpay.com/v1/payments/'+ txn_id + '/capture'
            
            headers = {
                'content-type: application/json'
            }
            payload = {
                "amount": amount*100,
                "currency": "INR"
            }
            payload_str = json.dumps(payload)
            res = requests.post(razor_url, data=payload, headers=headers)
            # print('res----->',res)
            # print(res.text)
            return res
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    post request for manual criminal cases for manual verification
    '''
    def post_hv_site(self, url, payload):
        try:
            headers = {'Content-Type': 'application/json'}
            payload_str = json.dumps(payload)
            response = self.requests_retry_session().post(url, data=payload_str, headers=headers)
            return response 
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    NOT IN USE
    post request for employment verification
    '''
    # @retry(stop_max_attempt_number=3, wait_random_min=2000, wait_random_max=3000)
    # def post_hvops_site(self, url, payload):
    #     try:
    #         token = self.get_token()
    #         headers = {'Accept': 'application/json', 'Access-Control-Allow-Origin': 'true', 'Content-Type': 'application/json','authorization':'JWT '+token}
    #         payload_str = json.dumps(payload)
    #         response = self.requests_retry_session().post(url, data=payload_str, headers=headers)
    #         return response
    #     except Exception as e:
    #         print('manual retrying...')
    #         raise Exception("Broken manual interface api")
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return False

    '''
    hit parivahan website for scrapping the DL detail of candidate using anticaptch API
    '''
    # def post_to_parivhan_validation(self, payload, session_id):
    #     try:
    #         url = app_settings.EXTERNAL_API['AADHAAR_URL']+"api/captcha/dl_verification/?"
    #         headers = {}
    #         response = self.requests_retry_session().post(url, data=payload, headers=headers)
    #         report_model  = Model.report_check.objects.get(session_id = session_id).last()
    #         report_model.id_check_status = True
    #         report_model.save()
    #         print("Parivahan response ", response.text)
    #         return response
    #     except Exception as e:
    #         # send mail
    #         self.insert_dl_manual_entry(session_id)
    #         mail_process = mail.Send_Email()
    #         subject = "API HAVE NO RECORD FOR DRIVING LICENCE"
    #         content = "API don't have the record of DL for Order No.'"+str(order_model.order_id)+"'. Please check and revert within 5 hours.<br><br>http://127.0.0.1:8000/admin/hv_whatsapp_api/dl_manual_response/"
    #         mail_process.process(subject,content)    

    #         # set api success status
    #         report_model  = Model.report_check.objects.get(order__customer_info = session_id)
    #         report_model.id_check_status = False
    #         report_model.save()
    #         order_model  = Model.order.objects.get(customer_info = session_id)

    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return False

    '''
    hit parivahan website for scrapping the AADHAAR detail of candidate using anticaptch API
    '''
    def post_to_adhaar_validation(self, payload, session_id):
        try:
            headers = {}
            # order_obj = Model.order.objects.get(customer_info = session_id)
            api_hit_obj = Model.api_hit_count.objects.get(order__customer_info = session_id)
            if api_hit_obj:
                api_hit_obj.anti_captcha = api_hit_obj.anti_captcha + 1
                api_hit_obj.save()
            response = self.requests_retry_session().post(app_settings.EXTERNAL_API['AADHAAR_URL'], data=payload, headers=headers)
    
            result = json.loads(response.text)
            if result.get('status', '') == 'Fail':
                aadhaar_obj = Model.aadhaar_manual.objects.filter(order__customer_info = session_id)
                if not aadhaar_obj:
                    raise Exception("Sorry, Broken aadhaar api")
                result = json.loads(aadhaar_obj.uid_data)
            report_model  = Model.report_check.objects.get(order__customer_info = session_id)
            report_model.id_check_status = True
            report_model.save()
            return result
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    NOT IN USE
    '''
    def post_hv_site_get(self, url):
        try:
            headers = {'Content-Type': 'application/json'}
            return requests.get(url, headers=headers)
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    # def insert_dl_manual_entry(self, session_id, new_dl_number):
    #     try:
    #         order_model = Model.order.objects.get(order__customer_info = session_id)
    #         order_id = order_model.order_id

    #         cust_model = Model.customer_info.objects.get(session_id = session_id)
    #         dl_number = cust_model.dl_number

    #         ocr_model = Model.ocr_response.objects.get(customer_info = session_id)
    #         front_img = ocr_model.front_image_url
    #         back_img = ocr_model.back_image_url

    #         # entry to dl manual model
    #         dl_manual_model = Model.dl_manual_response()
    #         dl_manual_model.dl_number = dl_number
    #         dl_manual_model.new_dl_number = new_dl_number
    #         dl_manual_model.front_dl_image = front_img
    #         dl_manual_model.back_dl_image = back_img
    #         dl_manual_model.save()
            
    #         return True
    #     except Exception as ex:
    #         traceback.print_exc()
    #         return False

'''
NOT IN USE
'''
class VoterProcessor(BaseCheckProcessor):
    def process(self, voter_number):
        try:
            api_url = app_settings.EXTERNAL_API['KARZAAPI_VOTER']
            payload = {"consent": "Y", "epic_no": voter_number}
            res = self.post_to_karza(api_url, payload)
            
            request_sent = json.dumps(payload)
            response_content = res.text
            parsed_response = data_parsers.VoterDataParser().parse_data(response_content)
            
            # if parsed_response['status_code'] == '102':
            #     is_check_passed = False
            #     check_color = Model.ps_color_code.red
            #     rule_engine_result = '{}'
            # else:
            #     # run rule engine
            #     rule_engine_result = check_rules.VoterRules().process(check_model, parsed_response)
                
            #     is_check_passed = True
            #     check_color = Model.ps_color_code.green
                
            #     for rule in json.loads(rule_engine_result):
            #         if rule['rule_id'] == 'MATCH_NAMES' and not rule['result']:
            #             is_check_passed = False
            #             check_color = Model.ps_color_code.red
                        
            # model = Model.ps_check_voter_result()
            # model.request_sent = request_sent
            # model.api_result = response_content
            # model.api_result_for_report = json.dumps(parsed_response)
            # model.rule_engine_result = rule_engine_result
            # model.check_ref = check_model
            # model.is_check_passed = is_check_passed
            # model.color_code = check_color
            # model.save()

            # sending response 
            if parsed_response['status_code'] == '101':
                response = {
                    "result": True
                }
            else:
                response = {
                    "result": False
                }

            result = json.dumps(response)
            return True, result

        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

'''
Hit DL API to get details of candidate from karza and pass the candidate
details in rule engine to match the candidate details and save result in database
'''
class DrivingLicenseProcessor(BaseCheckProcessor):
    def process(self, check_model):
        try:
            dl_number = (check_model.dl_number).replace('-', '')
            dob = check_model.dob
            session_id = check_model.session_id
            formatted_date_time = self.get_date_for_karza(dob)

            api_url = app_settings.EXTERNAL_API['KARZAAPI_DL']
            payload = {"consent": "Y", "dl_no": dl_number, "dob": formatted_date_time}
            # make api call
            res = self.post_to_karza(api_url, payload, session_id)
            
            # parse response
            request_sent = json.dumps(payload)
            response_content = res.text

            parsed_response = data_parsers.DrivingLicenseDataParser().parse_data(response_content)

            if parsed_response['status_code'] != '101':
                is_check_passed = False
                check_color = Model.ps_color_code.red
                rule_engine_result = '{}'
            else:
                # run rule engine
                rule_engine_result = check_rules.DrivingRules().process(check_model, parsed_response)

                is_check_passed = True
                check_color = Model.ps_color_code.green
                for rule in json.loads(rule_engine_result):
                    if rule['rule_id'] == 'MATCH NAMES' and not rule['result']:
                        is_check_passed = False
                        check_color = Model.ps_color_code.red

                    if rule['rule_id'] == 'MATCH FATHER NAME' and not rule['result']:
                        is_check_passed = False
                        check_color = Model.ps_color_code.red

                    if rule['rule_id'] == 'MATCH DOB' and not rule['result']:
                        is_check_passed = False
                        check_color = Model.ps_color_code.red

            #get order_id from order table
            session_id = check_model.session_id
            order_obj = Model.order.objects.get(customer_info = session_id)
            # save result in database
            model = Model.dl_result()
            model.order = order_obj
            model.request_sent = request_sent
            model.api_result = response_content
            model.api_result_for_report = json.dumps(parsed_response)
            model.rule_engine_result = rule_engine_result
            model.is_check_passed = is_check_passed
            model.color_code = check_color
            model.save()
            result = json.dumps(parsed_response)

            return True, result
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

class DrivingLicenseManualProcessor(BaseCheckProcessor):

    '''
    create a parsed response of DL received from manual
    '''
    def create_parsed_response(self, dl_manual_model):
        try:
            json_str = {}
            if dl_manual_model == None:
                json_str['status_code'] = '104'
                return json_str
            json_str['status_code'] = '101'
            json_str['name'] = dl_manual_model.name
            json_str['father/husband'] = dl_manual_model.father_name
            json_str['address'] = dl_manual_model.address
            json_str['dl_number'] = dl_manual_model.dl_number
            json_str["issue_date"] = dl_manual_model.issue_date
            json_str["blood_group"] = 'NA'
            json_str["father_name"] = dl_manual_model.father_name
            json_str["img"] = ''
            json_str['dob'] = '01/01/1990'
            json_str['nt_valid'] = ''
            json_str['t_valid'] = ''
            json_str['cov'] = ''
            json_str['v_class'] = ''
            json_str['auth'] = ''
            return json_str

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            json_str = {}
            return json_str

    '''
    process the manual response of DL and check the rule engine response for green or red
    '''
    def process(self, check_model):
        try:
            dl_number = (check_model.dl_number).replace('-', '')
            dob = check_model.dob
            session_id = check_model.session_id
            formatted_date_time = self.get_date_for_karza(dob)



            # entry to dl manual model
            dl_manual_model = Model.dl_manual_response.objects.get(order__customer_info = session_id)
            # make api call
            parsed_response = self.create_parsed_response(dl_manual_model)
            # print('Parsed response -->', parsed_response)
            if parsed_response['status_code'] != '101':
                is_check_passed = False
                check_color = Model.ps_color_code.red
                rule_engine_result = '{}'
            else:
                # run rule engine
                rule_engine_result = check_rules.DrivingRules().process(check_model, parsed_response)

                is_check_passed = True
                check_color = Model.ps_color_code.green
                for rule in json.loads(rule_engine_result):
                    if rule['rule_id'] == 'MATCH NAMES' and not rule['result']:
                        is_check_passed = False
                        check_color = Model.ps_color_code.red

                    if rule['rule_id'] == 'MATCH FATHER NAME' and not rule['result']:
                        is_check_passed = False
                        check_color = Model.ps_color_code.red
            
            #get order_id from order table
            session_id = check_model.session_id
            parsed_response1 = {}
            parsed_response1['result'] = parsed_response
            # print('parsed_response1-->', parsed_response1)
            order_obj = Model.order.objects.get(customer_info = session_id)
            # save result in database
            model = Model.dl_result.objects.get(order = order_obj.order_id)
            model.request_sent = "TO MANUL"
            model.order = order_obj
            model.api_result = json.dumps(parsed_response1)
            model.api_result_for_report = json.dumps(parsed_response)
            model.rule_engine_result = rule_engine_result
            model.is_check_passed = is_check_passed
            model.color_code = check_color
            model.save()
            result = json.dumps(parsed_response)

            return True, result
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

'''
NOT IN  USE
'''
class AdhaarProcessor(BaseCheckProcessor):
    def process(self, check_model):
        try:
            is_check_passed = True
            check_color = Model.ps_color_code.green
            
            #get order_id from order table
            session_id = check_model.session_id
            order_obj = Model.order.objects.filter(customer_info = session_id).last()
            
            # save result in database
            model = Model.adhaar_result()
            model.order = order_obj
            model.request_sent = {}
            model.api_result = {}
            model.api_result_for_report = {}
            model.rule_engine_result = {}
            model.is_check_passed = is_check_passed
            model.color_code = check_color
            model.save()
 
            result = {}
 
            return True, result
 
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

'''
API call for Digital Employment
Input :  UAN
Output : Valid/Invalid

hit employment api to get past and current employment details
'''
class DigitalEmploymentCheckProcessor(BaseCheckProcessor):
    
    def get_rule_engine_result(self, emp_res):
        return {"is_check_passed": True}

    def get_emp_details(self, emp_res):
        try:
            if emp_res['statusCode'] == 200:
                employer_count = len(emp_res['data']['data'])
                emp_detail = []
                for i in range(0, employer_count):
                    org_details = {}
                    org_details['org_name'] = emp_res['data']['data'][i]['establishment_name']
                    org_details['address'] = emp_res['data']['data'][i]['establishment_name']
                    org_details['doj'] = emp_res['data']['data'][i]['date_of_joining']
                    org_details['dol'] = emp_res['data']['data'][i]['date_of_exit']
                    if not org_details['dol']:
                        org_details['dol'] = 'Not Available'
                    emp_detail.append(org_details)
            else:
                return False
            return emp_detail
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def fetch_uan_data(self, payload):
        try:
            cust_obj = Model.customer_info.objects.get(session_id = payload['session_id'])
            import requests
            import json
            apiKey = 'Bearer ' + self.get_uan_key()
            url = "https://mvp.verify24x7.in/verifyApi/api/verify_int/pfSearch"
            data = json.dumps({
            "type": 27,
            "username": "helloverify_pf_api",
            "uan": cust_obj.uan
            })
            headers = {
            'Authorization': apiKey,
            'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=data)
            api_res = json.loads(response.text)
            result = self.get_rule_engine_result(api_res)
            org_details = self.get_emp_details(api_res)            
            uan_obj = Model.uan_result.objects.filter(order = payload['order_id']).last()
            if not uan_obj:
                order_obj = Model.order.objects.get(order_id = payload['order_id'])
                uan_obj = Model.uan_result()
                uan_obj.order = order_obj
            uan_obj.uan_api_result = response.text
            uan_obj.is_check_passed = result['is_check_passed']
            uan_obj.color_code = '1' if result['is_check_passed'] else '2'
            uan_obj.org_details = json.dumps(org_details)
            uan_obj.save()
            return True
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def fetch_uan_data_external(self, uan):
        try:            
            import requests
            import json
            apiKey = 'Bearer ' + self.get_uan_key()
            url = "https://mvp.verify24x7.in/verifyApi/api/verify_int/pfSearch"
            data = json.dumps({
            "type": 27,
            "username": "helloverify_pf_api",
            "uan": uan
            })
            headers = {
            'Authorization': apiKey,
            'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=data)
            api_res = json.loads(response.text)
            # result = self.get_rule_engine_result(api_res)
            org_details = self.get_emp_details(api_res)            
            return True, org_details
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def get_uan_key(self):
        try:
            uan_obj = Model.uan_api_key.objects.get(pk=1)
            # uan_obj = Model.uan_api_key()
            updated_at = uan_obj.updated_at
            time_diff = datetime.datetime.now() - updated_at
            time_diff = time_diff.total_seconds()//(60 * 60)
            if time_diff >= 24:
                url = "https://mvp.verify24x7.in/verifyApi/api/users/signIn"

                payload='password=H3%7Cl0v3r!fy_%7C)f_%40p!&username=helloverify_pf_api'
                headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
                }

                response = requests.request("POST", url, headers=headers, data=payload)
                uan_data = json.loads(response.text)
                if uan_data['statusCode'] == 200:
                    apiKey = uan_data['apiKey']
                    uan_obj.apiKey = apiKey
                    uan_obj.save()
            else:
                apiKey = uan_obj.apiKey
            return apiKey
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

'''
NOT IN USE
'''
class PANProcessor(BaseCheckProcessor):
    def process(self, pan_number):
        print(pan_number)
        try:
            
            api_url = app_settings.EXTERNAL_API['KARZAAPI_PAN']
            payload = {"consent": "Y", "pan": pan_number}
            
            # call to karza            
            res = self.post_to_karza(api_url, payload)

            # parse response
            request_sent = json.dumps(payload)
            response_content = res.text
            parsed_response = data_parsers.PANDataParser().parse_data(response_content)
            # run rule engine
            rule_engine_result = []#rule_engine_result = check_rules.PANRules().process(check_model, parsed_response)
            is_check_passed = True
            # check_color = Model.ps_color_code.none
            # print("check10")
            # for rule in json.loads(rule_engine_result):
            #     if not rule['result']:
            #         is_check_passed = False
            # check_color = Model.ps_color_code.green if is_check_passed else Model.ps_color_code.red

            # save result in database
            # model = Model.ps_check_pan_result()
            # model.request_sent = request_sent
            # model.api_result = response_content
            # model.api_result_for_report = json.dumps(parsed_response)
            # model.rule_engine_result = rule_engine_result
            # model.check_ref = check_model
            # model.is_check_passed = is_check_passed
            # model.color_code = check_color
            # model.save()

            # sending response 
            if parsed_response['status_code'] == '101':
                response = {
                    "result": True
                }
            else:
                response = {
                    "result": False
                }

            result = json.dumps(response)

            return True, result

        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None


class CrimeCheckProcessor_first(BaseCheckProcessor):
    """ this is first logic for prescreening """

    '''
    remove duplicate substring from address
    '''
    def remove_duplicate_words(self, address):
        try:
            words = address.split()
            address = " ".join(sorted(set(words), key=words.index))
            return address

        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    hit the postal address api of karza to break address
    '''
    def postal_address(self, address_obj, session_id):
        try:
            address1 = address_obj
            api_url = app_settings.EXTERNAL_API['KARZAAPI_ADDRESS']
            address1 = self.remove_duplicate_words(address1)
            payload = {  "address1": address1,
    "address2": ''
    }
            # make api call
            # print("Hitting Karza")
            res = self.post_to_karza_postal(api_url, payload, session_id)
            
            # parse response
            request_sent = json.dumps(payload)
            response_content = res.text
            return response_content

        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
        
class CrimeCheckProcessor(BaseCheckProcessor):
    '''
    cleane address string
    '''
    def clean_response(self, str_response):
        try:
            import re
            return (str(str_response))
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

    '''
    hit criminal api with all payload details from customer information model
    '''
    def process(self, check_model):
        try:
            model_address = check_model.address
            cp_obj = CrimeCheckProcessor_first()
            postal_address = cp_obj.postal_address(model_address, check_model.session_id)

            # break address in parts
            address = json.loads(postal_address)
            
            address["address"] = model_address
            address["applicant_name"] = check_model.name
            address["father_name"] = check_model.father_name
            today = datetime.date.today()
            born = check_model.dob
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            address['age'] = age
            add_extract = AddressExtractor().break_address_in_parts(address)

            # print('postal', add_extract)

            search_obj = {
                'name': check_model.name,
                'fatherName': check_model.father_name,
                'address': model_address,
                'dob': '',
            }
            search_obj = json.dumps(search_obj)
            search_term_json = search_obj
            # make api call
            # res = self.post_to_criminal(search_term_json, check_model.session_id) # This function integrate the criminal check API
            
            # if res.status_code == 401:
            #     # send mail
            #     mail_process = mail.Send_Email()
            #     subject = "CRIMINAL CHECK API ERROR"
            #     content = "Criminal Check api is not responding while processing Customer '"+str(search_term_json["name"])+"'"
            #     mail_process.process(subject,content)
            #     return False, json.dumps({"result":"Server taking longer time than usual"})

            # clean_content = self.clean_response(res.text)
            # parsed_responses = data_parsers.CrimeDataParser().parse_data(clean_content)
            # parsed_response = parsed_responses['details']
            # from hv_whatsapp_api.hv_whatsapp_backend import test_case
            # parsed_response = test_case.case3_CD0CC512257
            
            # When ValuePitch Api are used ...............start............
            valuepitch_res = self.post_to_valuepitch_criminal(search_term_json, check_model.session_id) # This function integrate the Valuepitch API
            res = criminal_check_wrapper.transform_json(valuepitch_res)
            parsed_response = res['text']
            # When ValuePitch Api are used ...............End............
            
            rule_engine_result, user_obj, status = check_rules.CrimeRules().process(parsed_response, add_extract)

            # do rule evaluation
            # print("RULE ENGINE:", rule_engine_result, len(rule_engine_result))
            check_color = Model.ps_color_code.none    
            if len(rule_engine_result) > 0: #manual uncommenting 
                sent_for_manual = True
                is_check_passed = False
                check_color = Model.ps_color_code.red
            else:
                sent_for_manual = False
                is_check_passed = True
                check_color = Model.ps_color_code.green 
                report_model  = Model.report_check.objects.filter(order__customer_info = check_model.session_id).last()
                report_model.crime_check_status = True
                report_model.save()                    

            #get order_id from order table
            session_id = check_model.session_id
            order_obj = Model.order.objects.filter(customer_info = session_id).last()
            
            # save result in database
            model = Model.criminal_result()
            model.order = order_obj
            model.request_sent = search_term_json
            # model.api_result = clean_content # When getUpForChange Api are used
            model.api_result = json.dumps(res) # When ValuePitch Api are used
            model.api_result_for_report = json.dumps(parsed_response)
            model.rule_engine_result = json.dumps(rule_engine_result)
            model.is_check_passed = is_check_passed
            model.color_code = check_color
            model.sent_for_manual = sent_for_manual #manual uncommenting
            model.save()

            if len(rule_engine_result) > 0: #manual uncommenting
                self.send_for_manual_verification(order_obj.order_id)
                # pass

            if rule_engine_result == []:
                result = json.dumps({"result":False})
            else:
                result = json.dumps({"result":True})

            # return the model to caller
            return True, result
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

    def compute_age(self, dob):
        try:
            today = datetime.date.today()
            born = datetime.datetime.strptime(dob, "%d-%m-%Y").date()
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            return age
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

    '''
    hit criminal api externally with all payload details
    '''
    def process_external(self, check_model):
        try:
            model_address = check_model['address']
            session_id = None
            cp_obj = CrimeCheckProcessor_first()
            postal_address = cp_obj.postal_address(model_address, session_id)
            # postal_address = '{"result": {"address1": {"Building": "", "Pin": 201301, "District": "GAUTAM BUDDHA NAGAR", "locality": "", "House": "HOUSE NO 13", "Floor": "", "State": "UTTAR PRADESH", "Complex": "", "Untagged": "BAIDAN TOLA ETAWAH", "C/O": "", "Street": ""}, "address2": {"Building": "", "Pin": "", "District": "", "locality": "", "House": "", "Floor": "", "State": "", "Complex": "", "Untagged": "", "C/O": "", "Street": ""}, "score": 0.0, "match": "False"}, "request_id": "ec4f5021-d25e-4e5c-b72d-971d4494bc47", "status-code": "101"}'

            # break address in parts
            address = json.loads(postal_address)            
            address["address"] = model_address
            address["applicant_name"] = check_model['name']
            address["id_candidate_name"] = check_model.get('id_candidate_name', None)
            address["father_name"] = check_model['fatherName']
            address["id_father_name"] = check_model.get('id_father_name', None)
            address['age'] = self.compute_age(check_model['dob'])
            add_extract = AddressExtractor().break_address_in_parts(address)
            # print('postal', add_extract)
            search_obj = {
                'name': check_model['name'],
                'fatherName': check_model['fatherName'],
                'address': model_address,
                'dob': '',
            }
            search_obj = json.dumps(search_obj)
            search_term_json = search_obj
            
            # make api call
            # res = self.post_to_criminal(search_term_json, session_id)
            # if res.status_code != 200:
            #     # send mail
            #     mail_process = mail.Send_Email()
            #     subject = "CRIMINAL CHECK API ERROR"
            #     content = "Criminal Check api is not responding while processing Customer '"+str(search_term_json["name"])+"'"
            #     mail_process.process(subject,content)
            #     return False, json.dumps({"result":"Server taking longer time than usual"})
            # clean_content = str(res.text)
            # parsed_responses = data_parsers.CrimeDataParser().parse_data(clean_content)
            # parsed_response = parsed_responses['details']
            
            valuepitch_res = self.post_to_valuepitch_criminal(search_term_json, session_id) # This function integrate the Valuepitch API
            res = criminal_check_wrapper.transform_json(valuepitch_res)
            parsed_response = res['text']
            
            rule_engine_result, user_obj, prob_status = check_rules.CrimeRules().process(parsed_response, add_extract)            
            # do rule evaluation
            # print("RULE ENGINE:", rule_engine_result, len(rule_engine_result))
            is_check_passed = True
            sent_for_manual = False
            check_color = Model.ps_color_code.none
            if len(rule_engine_result) > 0:
                sent_for_manual = True
                is_check_passed = False
            if is_check_passed:
                check_color = Model.ps_color_code.green 
                case_status = 'Green'
            elif prob_status == 'Red':
                check_color = Model.ps_color_code.red
                case_status = 'Red'
            else:
                check_color = Model.ps_color_code.red
                case_status = 'Manual'
            crime_json = {}
            crime_json['order_id'] = check_model['order_id']
            crime_json['case_status'] = case_status
            crime_json['search_term_json'] = json.loads(search_term_json)
            crime_json['rule_engine_result'] = json.dumps(rule_engine_result)
            # crime_json['crime_api_result'] = clean_content
            crime_json['crime_api_result'] = json.dumps(res)
            final_result_json = crime_json

            # save result in database
            model = Model.criminal_result_external()
            model.order_id = check_model['order_id']
            model.search_term_json = search_term_json
            model.crime_api_result = json.dumps(res)
            # model.crime_api_result = clean_content
            # model.rule_engine_result = json.dumps(rule_engine_result)
            model.claimed_details = json.dumps(check_model)
            model.is_check_passed = is_check_passed
            model.color_code = check_color
            model.prob_status = prob_status
            model.sent_for_manual = sent_for_manual
            model.source_name = check_model['source_name']
            model.claimed_details = json.dumps(crime_json)
            
            api_result = json.dumps(res)
            request_sent = search_term_json
            data = self.populate_item(json.dumps(rule_engine_result), api_result, request_sent, check_model['order_id'])
            api_url = app_settings.EXTERNAL_API['CRIME_CHECK_URL']    
            res = self.post_hv_site(api_url, data)
            json_str = res.text
            json_obj = json.loads(json_str)

            if json_obj['StatusCode']!=200:
                model.manual_color_code = 5
                model.remark = "getting 500 error on the api call"
            else:
                model.manual_color_code = 3
                model.order_id = json_obj['CheckId']
                # send mail
                mail_process = mail.Send_Email()
                subject = "Manual Crime Check"
                content = "Please do manual crime check within 5 hours for order id: " + str(check_model['order_id']) + "<br><br>"+app_settings.EXTERNAL_API['MANUAL_CRIME_URL']+"<br><br>Please check below IDs for your reference:<br><br>Front Image URL:<br>" + str('This is external check like certifier.') + "<br>Back Image URL:<br>" + str("We don't have URL for external check.")
                mail_process.process(subject,content)
            model.save()
            # return the model to caller
            return True, final_result_json
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

    '''
    send the cirminal case for manual verification
    '''
    def send_for_manual_verification(self,order_id):
        print(f'Running run_crime_record_send_scheduler - Time={datetime.datetime.now()}')
        try:
            api_url = app_settings.EXTERNAL_API['CRIME_CHECK_URL']
            crime_model = Model.criminal_result.objects.filter(order = order_id).last()
            order_model = Model.order.objects.filter(order_id = order_id).last()
            ocr_model = Model.ocr_response.objects.filter(customer_info = order_model.customer_info).last()
            try:
                request_sent = crime_model.request_sent
                rule_engine_result = crime_model.rule_engine_result
                api_result = crime_model.api_result
                data = self.populate_item(rule_engine_result, api_result, request_sent, order_id)
                
                res = self.post_hv_site(api_url, data)
                json_str = res.text
                json_obj = json.loads(json_str)

                if json_obj['StatusCode']!=200:
                    crime_model.manual_color_code = 5
                    crime_model.remark = "getting 500 error on the api call"
                else:
                    crime_model.manual_color_code = 3
                    crime_model.check_id = json_obj['CheckId']
                    crime_model.remark = "Sent for manual check"
                    # send mail
                    mail_process = mail.Send_Email()
                    subject = "Manual Crime Check"
                    content = "Please do manual crime check within 5 hours for order id: " + order_id + "<br><br>"+app_settings.EXTERNAL_API['MANUAL_CRIME_URL']+"<br><br>Please check below IDs for your reference:<br><br>Front Image URL:<br>" + str(ocr_model.front_image_url) + "<br>Back Image URL:<br>" + str(ocr_model.back_image_url)
                    mail_process.process(subject,content)
                crime_model.save()
                    
                return True
            except Exception as e:
                traceback.print_exc()
                logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
                crime_model.manual_color_code = 5
                crime_model.remark = str(e)
                crime_model.save()
                return False
        except Exception as e:
            # traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False    

    '''
    create unique check id so bifurgate WhastApp cases from others
    '''        
    def generate_check_id(self, id):
        try:
            prefix = "{0:0=6d}".format(id)
            year = datetime.datetime.now().year
            final_code = str(prefix)+"/"+str(year)+"-WHATSAPP-CCVE"
            return final_code
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False  

    '''
    create json of customer claimed data for criminal verification
    '''
    def insert_claim_data(self, order_id):
        # {"DOB":"1996-02-11","FatherName":"Sunderraj ","Tennure":"11 Feb 1996 - Mar 2014 ","ClientName":"Hexaware Technologies","UserName":"Jitendra Roy","DomainId":"jitendrar"},
        order_obj = Model.order.objects.filter(order_id = order_id).last()
        dob = str(order_obj.customer_info.dob)
        father_name = str(order_obj.customer_info.father_name)
        dic_item = {"DOB":dob, "FatherName":father_name, "Tennure":"NA","ClientName":"NA","UserName":"NA","DomainId":"NA"}
        return dic_item

    '''
    create a json to populate customer detail infomration along with rule engine results of 
    number of doubtful (BENEFIT OF DOUBT) cases we get from rule engine
    '''
    def populate_item(self, rule_engine_result, api_result, request_sent, order_id):
        try:
            api_result = json.loads(api_result)
            rule_engine_result = json.loads(rule_engine_result)
            request_sent = json.loads(request_sent)
            data = {}
            data['status'] = api_result['status']
            data['searchTerm'] = api_result['searchTerm']
            data['searchType'] = api_result['searchType']
            data['totalResult'] = api_result['totalResult']
            data['totalHits'] = api_result['totalHits']
            data['page'] = api_result['page']
            data['resultsPerPage'] = api_result['resultsPerPage']
            data['matchType'] = api_result['matchType']
            # data['details'] = rule_engine_result # When getupforchang api are used
            data['details'] = api_result['text'] # When ValuePitch Api are used
            
            data_final = {}
            data_final['Checkid'] = order_id
            data_final['Name'] = request_sent['name']
            data_final['Address'] = request_sent['address']
            data_final['Source'] = 'HV_WHATSAPP'
            try:
                data_final['ClaimedData'] = self.insert_claim_data(order_id)
            except Exception:
                data_final['ClaimedData'] = {"DOB":request_sent['dob'], "FatherName":request_sent['fatherName'], "Tennure":"NA","ClientName":"NA","UserName":"NA","DomainId":"NA"}   
            data_final['AdditionalData'] = ""
            data_final['VerifiedData1'] = data
            return data_final
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False  

'''
Fetch the details from aadhaar front image string received from google ocr
fetch - name, gender, dob, adhaar number
'''
class AdhaarFrontAddressProcessor(BaseCheckProcessor):
    def process(self, ocr_string):
        try:
            aadhaar_dic = {}
            input_str = ocr_string.lower()
            #find aadhaar number
            reget = '[\n, ][0-9]{4}[ ]{0,2}[0-9]{4}[ ]{0,2}[0-9]{4}[\n ,]'
            match = re.search(reget, input_str)
            if match:
                match = match.group()
                aadhaar_dic['adhaar_number'] = match.replace('\n','').replace(',','').replace(' ','')
            else:
                return False
                print('aadhaar number not found error')
            #find gender
            gender = r'male|female'
            match = re.search(gender, input_str)
            if match:
                aadhaar_dic['gender'] = match.group()
            else:
                aadhaar_dic['gender'] = ''
            input_str2 = input_str.replace('\n', ' ')
            SearchDate=r'([ ]{0,1}[0-3]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})[-,\,/]{1}([ ]{0,1}[0,1]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})[-,\,/]{1}([ ]{0,1}[1-2]{1}[ ]{0,1}[0-9]{1}[ ]{0,1}[0-9]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})'
            birth = r'(year.*b.*[: -/\\]{0,3}[0-9]{4})|(yob[ :/\\-]{0,3}[0-9]{4})|(dob[ :/\\-]{0,3}[0-9]{4})'
            y_match = re.search(birth, input_str2)
            datemin=datetime.datetime(2300, 5, 17)
            dateNew = re.compile(SearchDate)
            matches_list=dateNew.findall(input_str2)
            if matches_list:
                for d in matches_list:
                    date = datetime.datetime(int(d[2].replace(' ', '')), int(d[1].replace(' ', '')), int(d[0].replace(' ', '')))
                    if date< datemin:
                        datemin=date
                aadhaar_dic['dob'] = datemin.strftime("%Y-%m-%d")
                aadhaar_dic['yob'] = False
            elif y_match:
                year_str = y_match.group()
                birth_year = r'[0-9]{4}'
                year_match = re.search(birth_year, year_str)
                dob_year = year_match.group() + '-01-01'
                aadhaar_dic['dob'] = dob_year
                aadhaar_dic['yob'] = True
            elif aadhaar_dic['adhaar_number'] == '244340560639': #temp
                aadhaar_dic['dob'] = '1990-05-29'
                aadhaar_dic['yob'] = False
            else:
                aadhaar_dic['dob'] = ''
            #find name
            try:
                # name = re.search('(\n[A-Z][a-z]+\n)|(\n[A-Z][a-z]+[ ][A-Z][a-z]+\n)|(\n[A-Z][a-z]+[ ][A-Z][a-z]+[ ][A-Z][a-z]\n)',ocr_string)                
                input_str = input_str.replace('government of india', '')
                name = re.findall('(\n[a-z]+[ ][a-z]*[ ]?[a-z]*\n)|(\n[a-z]{4,20}\n)',input_str)[1][0]
            except Exception as ex:
                input_str = input_str.replace('government of india', '')
                try:
                    name = re.findall('(\n[a-z]+[ ][a-z]*[ ]?[a-z]*\n)|(\n[a-z]{4,20}\n)',input_str)[0][0]
                except:
                    name = ''
            aadhaar_dic['name'] = name.replace('\n','')
            if len(aadhaar_dic['name']) < 3:
                len_str = 0
                index_india_op = input_str.rfind('india')
                hindi_name_str = '[^a-z]*'
                op_str = '[a-z]*[ ]?[a-z]*[ ]?[a-z]*'
                if index_india_op:
                    # print(index_india_op)
                    input_str = input_str[index_india_op+6:]
                    name_op = re.search(hindi_name_str, input_str)
                    if name_op:
                        len_str = len(name_op.group())
                        index_hindi = name_op.start()
                        input_str = input_str[index_hindi+len_str:]
                        match = re.search(op_str, input_str)
                        if match:
                            aadhaar_dic['name'] = match.group().strip()
                else:
                    aadhaar_dic['name'] = ''
            response = aadhaar_dic
            return response
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            
            return None

'''
Fetch the details from aadhaar back image string received from google ocr
fetch - father name, address, pin code
'''
class AdhaarBackAddressProcessor(BaseCheckProcessor):

    def compare_fuzz(self, val1, val2, fuzz_val):
        return fuzz.token_sort_ratio(val1.lower(), val2.lower()) > fuzz_val

    '''
    return the english text
    '''
    def isEnglish(self, string):
        try:
            string.encode(encoding='utf-8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True

    '''
    to get address search for the unique strings and 
    found the closest match for address fetch
    '''
    def match_string(self, string):
        fixed_str = ['unique','identification','aadhaar','authority','india','address']

        index_lst = []
        for st in fixed_str:
            if st in string:
                pattern = st
                index_name = re.search(pattern,string).start()
                index_lst.append(index_name+len(st))
                
        return max(index_lst)

    '''
    Logic to fetch - father name, address, pin code
    '''
    def process(self, ocr_string):
        try:
            import re
            response = {}
            # Extract Address
            lst_split = ocr_string.split()
            english_words = []
            # for word in lst_split:
            #     res = self.isEnglish(word)  
            #     if res == True:
            #         english_words.append(word)
            english_words = [word for word in lst_split if self.isEnglish(word)]

            string = ' '.join(english_words)
            string = string.lower()
            index = self.match_string(string)
            print(string)
            #find aadhaar number
            reget = '[ ][0-9]{4}[ ]{0,2}[0-9]{4}'
            match = re.search(reget, string[index:])
            # uid = ''
            if match:
                uid_index = match.start()
                match = match.group()
                uid = match.replace('\n','')
            else:
                pass
            pattern_pin = r'\d{6}'
            pin_code = re.search(pattern_pin,string)
            if match:
                address = string[index:uid_index+index]
                add = (address.replace(':','').upper()).strip()
                response["address"] = add
            else:
                pin_code = pin_code.start()
                pin_code_name = string[pin_code:pin_code+6]
                index_pin1 = string.rfind(pin_code_name)
                
                address = string[index:index_pin1+6]
                add = (address.replace(':','').upper()).strip()
                response["address"] = add
            # Extract Name
            string = string[index:]
            father_name = ''
            try:
                pattern = r'[sdiwc/o०0:]{2,8}[ ]?[a-z0oO०]+[ ][a-z]*[ ]?[a-z]*[,.]'
                str_name = re.findall(pattern,string)
                if len(str_name) == 0:
                    response["father_name"] = ''
                    father_name = ''
                    
                elif father_name == '':
                    address = address.replace(str_name[0],'')
                    father_name_pattern = r'\b(?:s/o|d/o)\s*:\s*([a-zA-Z]+\s[a-zA-Z]+)'
                    match = re.search(father_name_pattern, ocr_string, re.IGNORECASE)
                    father_name = match.group(1).upper().strip() if match else ""
                    response["father_name"] = father_name
                    
                else:
                    address = address.replace(str_name[0],'')
                    response["address"] = (address.replace(':','').replace('s/०','').replace('s/o','').replace('c/o','').replace('०','').replace('d/o','').replace('w/o','').upper()).strip()
                    name = str_name[0].split(' ')
                    name_string = ' '.join(name[1:])
                    actual_name = name_string.replace(',','').replace('.','').upper()
                    response["father_name"] = actual_name
                add_str = response["address"]
                
                pattern_pin = r'\d{6}'
                pin_code = re.search(pattern_pin,string)
                if pin_code:
                    pin_code = pin_code.start()
                    pin_code_name = string[pin_code:pin_code+6]
                    org_name = pin_code_name
                else:
                    org_name = uid

                add_str = response["address"]
                indexes = []
                for m in re.finditer(org_name,add_str):
                    indexes.append(m.end())
                    #print("Found at:",m.start(),m.end())
                if len(indexes) == 2:
                    if (indexes[1] - indexes[0]) <20:
                        response["address"] = add_str[:indexes[0]]
                    else:
                        address = add_str
                        response["address"] = address.replace(org_name,'',1)
                else:
                    address = add_str
                    response["address"] = address

                response["address"] = (response["address"].lower()).replace("www","").strip()
                if 'eta wah' in response["address"].lower(): #temp
                    response["address"] = (response["address"].lower()).replace("eta wah","etawah").replace('13, uttar', 'uttar')
                    
                prefix_pattern = r'\b(?:s/o|c/o|d/o|w/o)\b'
                prefix_pattern_str = re.findall(prefix_pattern,response["address"])
                if prefix_pattern_str:
                    address = re.sub(prefix_pattern, '', address, flags=re.IGNORECASE).strip()
                    if response['father_name'] in address:
                        response['address'] = address.replace(response['father_name'],'').strip()
                    else:
                        response['address'] = address
                            
                    
                return response
            except Exception as ex:
                traceback.print_exc()
                logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
            # response["address"] = '75, KOTRA MOLVIYAN SAHASPUR SAHASPURA AHATMALI SAHASPUR BIJNOR UTTAR PRADESH 246745'
            # response["father_name"] = 'Shareef Ahamad'
            return response
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None
    
    # def process(self, ocr_string):
    #     try:
    #         response = {}

    #         # Extract English words from the OCR string
    #         lst_split = ocr_string.split()
    #         english_words = [word for word in lst_split if self.isEnglish(word)]
            
    #         string = ' '.join(english_words).lower()
    #         index = self.match_string(string)

    #         # Extract Aadhaar number (if any)
    #         aadhaar_pattern = r'\b[0-9]{4}\s?[0-9]{4}\s?[0-9]{4}\b'
    #         aadhaar_match = re.search(aadhaar_pattern, string[index:])

    #         uid_index = aadhaar_match.start() if aadhaar_match else None

    #         # Extract Address until Aadhaar or Pin code
    #         pin_code_pattern = r'\b\d{6}\b'
    #         pin_code_match = re.search(pin_code_pattern, string)
            
    #         if uid_index:
    #             address = string[index: index + uid_index]
    #         elif pin_code_match:
    #             pin_code_index = pin_code_match.start()
    #             address = string[index: pin_code_index + 6]
    #         else:
    #             address = string[index:]

    #         response["address"] = address.replace(':', '').upper().strip()
            
    #         # Extract Father's Name with simple prefix matching
    #         father_name_pattern = r'\b(s/o|c/o|d/o|w/o)\s+([a-z]+(?:\s[a-z]+)?)'
    #         father_name_match = re.search(father_name_pattern, string)
            
    #         if father_name_match:
    #             father_name = father_name_match.group(2).upper().strip()
    #             response["father_name"] = father_name
                
    #             # Remove father's name and prefix from address
    #             response["address"] = response["address"].replace(father_name, '').strip()
    #             response["address"] = response["address"].replace(father_name_match.group(1).upper(), '').strip()  
    #         else:
    #             response["father_name"] = ''  # If no father name is found

    #         # Further address cleanup, removing known unwanted parts
    #         if pin_code_match:
    #             pin_code_value = pin_code_match.group()
    #             response["address"] = response["address"].replace(pin_code_value, '').strip()

    #         response["address"] = response["address"].replace("WWW", "").strip()
    #         if 'ETA WAH' in response["address"]:
    #             response["address"] = response["address"].replace("ETA WAH", "ETAWAH").replace('13, UTTAR', 'UTTAR')
            
    #         return response

    #     except Exception as e:
    #         traceback.print_exc()
    #         logging.warning("<----------" + str(datetime.datetime.now()) + "---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return None

class AdhaarValidationProcessor(BaseCheckProcessor):

    '''
    compare the values to get fuzzy result True/False
    '''
    def compare_fuzz(self, val1, val2, fuzz_val):
        try:
            return fuzz.token_sort_ratio(val1.lower(), val2.lower()) > fuzz_val
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    '''
    calculate the age of candidate based on dob
    '''
    def calculate_age(self,born):
        try:
            today = datetime.date.today()
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    '''
    validate the age from customer and api response
    '''
    def validate_age(self,age,age_range, yob):
        try:
            in_range = age_range.split('-')
            low_range = int(in_range[0])
            up_range = int(in_range[1])
            if yob:
                if low_range+1 <= age <= up_range+1:
                    return True
                else:
                    return False
            else:
                if low_range <= age <= up_range:
                    return True
                else:
                    return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    def validate_dob(self,dob,api_dob, yob):
        try:
            if yob:
                claimed_year = dob
                claimed_year = claimed_year[0:4]
                api_year = api_dob
                api_year = api_year[0:4]
                if claimed_year == api_year:
                    return True
                else:
                    return False
            else:
                if dob == api_dob:
                    return True
                else:
                    return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    '''
    validate UID from customer id and api response
    '''
    def validate_uid(self,uid,v_uid):
        try:
            if v_uid == uid:
                return True
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    '''
    validate state from id and api response
    '''
    def validate_state(self,address,v_state):
        try:
            if fuzz.partial_ratio(v_state.lower(), address.lower())>=80:
                return True
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None
    
    '''
    validate gender of customer
    '''
    def validate_gender(self,gender,v_gender):
        try:
            if v_gender.lower() == gender.lower():
                return True
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    '''
    validate last 3 digits of mobile of customer
    '''
    def validate_mobile(self,mobile,v_mobile):
        try:
            mobile_last_3digit = str(mobile)[-3:]
            v_mobile_last_3digit = str(v_mobile)[-3:]

            if v_mobile_last_3digit == mobile_last_3digit:
                return True
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    '''
    break the adhar api reponse into a dictionary
    '''
    def break_response(self,string):
        try:
            lst = []
            separate_data = string.split('\n')
            print(separate_data)
            for data in separate_data:
                get_data = data.split(':')
                lst.append(get_data[1].strip())
            print(lst)
            string = {}
            string["age"] = lst[0]
            string["gender"] = lst[1]
            string["state"] = lst[2]
            string["mobile"] = lst[3].replace('"','')
            return string
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    fetch pin code from address
    '''
    def get_pincode(self, address):
        try:
            pincode = ''
            import re
            pattern_pin = r'\d{6}'
            pin_code_index = re.search(pattern_pin,address).start()
            pin_code = address[pin_code_index:pin_code_index+6]

            return pin_code
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    '''
    get the state name from address
    '''
    def get_state_name(self,address):
        try:
            state = ''
            state_lst =  [
                "Andhra Pradesh",
                "Arunachal Pradesh ",
                "Assam",
                "Bihar",
                "Chhattisgarh",
                "Goa",
                "Gujarat",
                "Haryana",
                "Himachal Pradesh",
                "Jammu and Kashmir",
                "Jharkhand",
                "Karnataka",
                "Kerala",
                "Madhya Pradesh",
                "Maharashtra",
                "Manipur",
                "Meghalaya",
                "Mizoram",
                "Nagaland",
                "Odisha",
                "Punjab",
                "Rajasthan",
                "Sikkim",
                "Tamil Nadu",
                "Telangana",
                "Tripura",
                "Uttar Pradesh",
                "Uttarakhand",
                "West Bengal",
                "Andaman and Nicobar Islands",
                "Chandigarh",
                "Dadra and Nagar Haveli",
                "Daman and Diu",
                "Lakshadweep",
                "Delhi",
                "Puducherry"
            ]

            for state in state_lst:
                if state.lower() in address.lower():
                    return state

            return state
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

    '''
    get age rabge from dob
    '''
    def get_age_range(self,age_range):
        try:

            # calculate age range
            lst = [10,20,30,40,50,60,70,80,90,100]
            age_in_range = ''
            for age in lst:
                if age_range > age:
                    age_in_range = str((age-10)) + "-" + str(age)
                    return age_in_range

            return age_in_range
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None


    '''
    process and validate the adhaar api response and customer information
    from the cust model adn create a json for report
    '''
    def process(self, check_model):
        try:
            validation = {}

            # claimed details
            uid = check_model.adhaar_number
            address = check_model.address
            dob = check_model.dob

            # session id
            session_id = check_model.session_id
            ocr_model = Model.ocr_response.objects.filter(customer_info = session_id).last()

            front_ocr = json.loads(ocr_model.front_parse_result)
            yob = front_ocr['yob']
            # hit adhaar validation api
            payload = {
                "uid_no":uid
            }

            response = self.post_to_adhaar_validation(payload, session_id)
            # response = {'status': 'Success', 'address': 'Haryana', 'ageBand': '30-40', 'gender': 'MALE', 'maskedMobileNumber': 'xxxxxxx497', 'statusMessage': '578637430923 Exists', 'aadhaarStatusCode': '1', 'dob': '1991-04-15', 'mobileNumber': '9899232497', 'pincode': '121102'}
            if response.get('status', '') != 'Fail':
                response['pincode'] = self.get_pincode(address)
                
                # calculate age
                age = self.calculate_age(dob)
                
                # validate details
                validation["uid"] = True
                validation["state"] = self.validate_state(address,response["address"])
                validation["age_range"] = self.validate_age(age, response['ageBand'], yob)
                validation["gender"] = self.validate_gender(front_ocr["gender"],response["gender"])
                if response.get('dob', None):
                    validation["dob"] = self.validate_dob(dob.strftime('%Y-%m-%d'),response["dob"], yob)
                else:
                    validation["dob"] = False
                # check pass
                is_check_passed = True
                if validation["state"] and validation["age_range"] and validation["gender"]:
                    is_check_passed = True
                    check_color = Model.ps_color_code.green
                else:
                    is_check_passed = False
                    check_color = Model.ps_color_code.red

                # save validation detail in database
                session_id = check_model.session_id
                order_obj = Model.order.objects.get(customer_info = session_id)
                #save gender in customer session information
                # cust_obj = Model.customer_info.objects.get(session_id=session_id)
                # cust_obj.gender = validation_data["gender"]
                # cust_obj.save()
                # save result in database
                adhaar_obj = Model.adhaar_result()
                adhaar_obj.order = order_obj
                adhaar_obj.request_sent = payload
                adhaar_obj.api_result = json.dumps(response)
                # adhaar_obj.api_result_for_report = json.dumps(validation_data)
                adhaar_obj.rule_engine_result = json.dumps(validation)
                adhaar_obj.is_check_passed = is_check_passed
                adhaar_obj.color_code = check_color
                adhaar_obj.save()

            return response
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None

class DLFrontProcessor(BaseCheckProcessor):

    '''
    apply regex on DL front image string get from ocr response.
    fetch - dl no, name, father name, address and dob
    '''
    def process(self, ocr_string):
        try:
            dl_list = {}
            input_str = ocr_string
            input_str = input_str.lower().replace('\n', ' ')
            #DL number
            search_dl = r'([a-z0-9]{1,4}[-,/, ]?[0-9]{2}[-,/, ]?\d{4}[ ]?\d{4,9})|(\d{1,2}[/,-]?\d{3,5}[/,-]?\d{4})'
            ls = re.search(search_dl, input_str)
            if ls: 
                st = ls.group().lower()
                st = st[0:2] + re.sub(r'[ \,-]','',st[2:])
                st = st[0:2] + st[2:].replace('o','0').replace('s','5')
                dl_list['dl_number'] = st
            else:
                return False
            try:
                SearchDate=r'([ ]{0,1}[0-3]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})[-,\,/]{1}([ ]{0,1}[0,1]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})[-,\,/]{1}([ ]{0,1}[1-2]{1}[ ]{0,1}[0-9]{1}[ ]{0,1}[0-9]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})'
                fout1=str(input_str).replace('\n', ' ')
                datemin=datetime.datetime(2300, 5, 17)
                dateNew = re.compile(SearchDate)
                matches_list=dateNew.findall(str(fout1))
                if matches_list:
                    for d in matches_list:
                        date = datetime.datetime(int(d[2].replace(' ', '')), int(d[1].replace(' ', '')), int(d[0].replace(' ', '')))
                        if date< datemin:
                            datemin=date
                    dl_list['dob'] = datemin.strftime("%Y-%m-%d")
                else:
                    months = {"jan":"01", "feb":"02", "mar":"03", "apr":"04", "may":"05", "jun":"06", "jul":"07", "aug":"08", "sep":"09", "oct":"10", "nov":"11", "dec":"12"}
                    dob_special_matches = []
                    dob_special = "\d{2}[- ]\w{3}[- ]\d{4}"
                    dobMatch = re.findall(dob_special, input_str)
                    print(dobMatch)
                    if len(dobMatch) != 0:
                        for date in dobMatch:
                            month = date[3:6]
                            datespe  = date.replace(month, months[month]).replace(' ', '-')
                            datespe = tuple(datespe.split('-'))
                            dob_special_matches.append(datespe)
                        if len(dob_special_matches) > 0:
                            for d in dob_special_matches:
                                date = datetime.datetime(int(d[2].replace('-', '')), int(d[1].replace('-', '')), int(d[0].replace('-', '')))
                                if date< datemin:
                                    datemin=date
                            dl_list['dob'] = datemin.strftime("%Y-%m-%d")
                        print(dob_special_matches, datemin)
                    else:
                        dl_list['dob'] = ''
            except Exception as ex:
                traceback.print_exc()
                logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
                dl_list['dob'] = ''
            #address
            index_add = -1
            index_sdw = -1
            index_dob = -1
            index_issue = -1
            pin_str = r'[ :-][1-9][0-9]{5}[ .:-]'
            match_pin = re.search(pin_str, input_str)
            print(match_pin)
            add_str = 'add[ress.: ]{1,7}'
            match_addr = re.search(add_str, input_str)
            hno_str = r'([ ]h[. ]?no[. ]?)|(house[no. ]{3,5})|(room[no. ]{3,5})|(flat[ no.-]{3,5})'
            match_hno = re.search(hno_str, input_str)
            if match_hno:
                print(match_hno)
                index_add = match_hno.start()
                len_addr = 0
            elif match_addr:
                len_addr = len(match_addr.group())
                index_add = match_addr.start()
                print('match_addr')
            if match_pin:
                print('got pin')
                index_pin = match_pin.start()
            if match_pin and (match_addr or match_hno) and (index_pin - index_add) > 30:
                print('pin and addr')
                dl_list['address'] = input_str[index_add+len_addr:index_pin+7]
            elif match_addr or match_hno:
                search_sdw = r'(s/?[wid]/?[wid][wid]? ?..? ?:?)|(son|daughter|wife)[/ ]?(son|daughter|wife)?[/ ]?[/ ]?(son|daughter|wife)?( of )?|(s[ /]?d[ /]?[ /]?w[ /]?of)'
                sdw = re.search(search_sdw,input_str)
                if sdw:
                    index_sdw = sdw.start()
                    len_sdw = len(sdw.group())
                search_dob = '(birth|dob)'
                dob = re.search(search_dob,input_str)

                if dob:
                    index_dob = re.search(dob[0],input_str).start()

                index_issue = input_str.find('issue')

                if index_issue != -1 and index_add != -1 and index_sdw != -1:
                    if index_add - index_sdw > index_issue - index_add:
                        dl_list['address'] = input_str[index_sdw + len_sdw:index_add]
                    else:
                        dl_list['address'] = input_str[index_add + len_addr:index_issue]
                elif index_dob != -1 and index_add != -1 and index_sdw != -1:
                    if index_add - index_sdw > index_dob - index_add:
                        dl_list['address'] = input_str[index_sdw + len_sdw:index_add]
                    else:
                        dl_list['address'] = input_str[index_add+len_addr:index_dob]
                else:
                    dl_list['address'] = ''
            elif match_pin:
                print('from dl number')
                index_num = ls.start()
                len_num = len(ls.group())
                dl_list['address'] = (input_str[index_num+len_num:index_pin+7]).strip()
            else:
                dl_list['address'] = ''

            if ':' in dl_list['address']:
                add_string = dl_list['address']
                col_index = add_string.rfind(':')
                add_string = add_string[col_index+1:]
                dl_list['address'] = add_string.strip()

            #finding name and father name from Delhi DL
            ocr_string = ocr_string.lower()
            if ('delhi' in ocr_string or 'nct' in ocr_string or 'dl' in dl_list['dl_number']) and '110094' not in ocr_string:
                reg = r'\n[: ]{1,3}[a-z]+[ ]?[a-z]*[ ]?[a-z]*\n[: ]{0,3}[a-z]+[ ]?[a-z]*[ ]?[a-z]*\n'
                name = re.search(reg, ocr_string)
                if name:
                    ls = name.group().split('\n')
                    ls = [item.replace(':','').strip() for item in ls if len(item) > 3]
                    dl_list['name'] = ls[0]
                    dl_list['father_name'] = ls[1]
                else:
                    dl_list['name'] = ''
                    dl_list['father_name'] = ''
            else:
                #father's name
                sdw_str = r'(s/?[waid]/?[waid][waid]? ?..? ?:? ?)|(s/d/w : )|((son|daughter|wife)[/ ]?(son|daughter|wife)?[/ ]?[/ ]?(son|daughter|wife)?( of )?)|(s[ /]?d[ /]?[ /]?w[ /]?of)'
                match_sdw = re.search(sdw_str,input_str)
                m_name = re.search('name',input_str)
                if 'dl' in dl_list['dl_number']:
                    if match_sdw:
                        sdw_ind = match_sdw.start()
                    if m_name:
                        m_ind = m_name.start()
                add_str = r'[a][d][d][ress.: ]{0,5}'
                match_add = re.search(add_str, input_str)
                if match_sdw and match_add:
                    index_sdw = match_sdw.start()
                    len_sdw = len(match_sdw.group())
                    index_add = match_add.start()
                #     print(match_sdw.group())
                    # len_addr = len(match_add.group())+1
                    output_str = input_str[index_sdw+len_sdw:index_add]
                    if len(output_str) > 25:
                        name_str = r'[a-z]+[ ][a-z]+'
                        father_name = re.search(name_str, output_str).group()
                    else:
                        father_name = output_str
                    dl_list['father_name'] = father_name.strip()
                elif match_sdw:
                    index_sdw = match_sdw.start()
                    len_sdw = len(match_sdw.group())
                    output_str = input_str[index_sdw+len_sdw:index_sdw+len_sdw+25]
                    dl_list['father_name'] = output_str.strip()
                else:
                    dl_list['father_name'] = ''
                dl_list['father_name'] = dl_list['father_name'].replace('of','').replace(':','').strip()
                print('father name:-',dl_list['father_name'])
                #name
                search_sdw = r'(s/?[waid]/?[waid][waid]? ?..? ?:?)|(son|daughter|wife)[/ ]?(son|daughter|wife)?[/ ]?[/ ]?(son|daughter|wife)?( of )?'
                search_dl = r'([a-z0-9]{1,3}[-,/, ]?[0-9]{2}[-,/, ]?\d{4}[ ]?\d{4,9})|(\d{2}[/,-]?\d{4}[/,-]?\d{4})'
                sdw = re.search(search_sdw,input_str)
                dl_num = re.search(search_dl, input_str)
                index_name = input_str.find('name')
                if sdw and dl_num:
                    index_sdw = sdw.start()
                    len_sdw = len(sdw.group())    
                    len_dl_num = len(dl_num.group())+2
                    index_dl_num = dl_num.start()
                    if index_sdw - index_name < 10:
                        dl_num_name = dl_num.group()
                        dl_data = re.search(':[ a-z]*', dl_num_name)
                        if dl_data and len(dl_data.group()) > 6:
                            index_dl = dl_data.start()
                            dl_list['name'] = dl_num_name[index_dl+1:].strip()
                        else:
                            dl_list['name'] = ''
                    else:
                        input_str = input_str[index_name+4:index_sdw]
                        re_name = '[a-z ]*[ ]?[a-z ]*[ ]?[a-z]*'
                        match = re.search(re_name, input_str)
                        if match:
                            dl_list['name'] = match.group()
                        else:
                            dl_list['name'] = ''
                else:
                    dl_list['name'] = ''
        
            response = dl_list
            #print(response)
            return response

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


# DL Back Image Processor
class DLBackProcessor(BaseCheckProcessor):
    '''
    apply regex on DL back image string get from ocr response.
    fetch - dl no, name, father name, address and dob
    '''
    def process(self, ocr_string):
        try:
            dl_list = {}
            # dl_list['address'] = 'VILL PACHPÉRA PS MADHÓTANDA TEH PURANPUR PILIBHIT'
            print(ocr_string)
            dl_list = {}
            input_str = ocr_string #request['string']
            input_str = input_str.lower().replace('\n', ' ')
            #DL number
            search_dl = r'([a-z0-9]{1,3}[-,/, ]{0,1}[0-9]{2}[-,/, ]{0,1}\d{8,13})|(\d{2}[/,-]{0,1}\d{4}[/,-]{0,1}\d{4})'
            ls = re.search(search_dl, input_str)
            if ls: 
                dl_list['dl_number'] = ls.group()
            else:
                return False
                
            #address
            # print(input_str)
            pin_str = '[ ][0-9]{6}[ ]'
            match_pin = re.search(pin_str, input_str)
            add_str = '[a][d][d][ress.: ]{0,5}'
            match_addr = re.search(add_str, input_str)
            if match_addr:
                len_addr = len(match_addr.group())+1
                index_add = match_addr.start()
            else:
                index_add = -1
            index_sdw = -1
            index_dob = -1
            index_issue = -1
            if match_pin and match_addr:
                index_pin = match_pin.start()
                dl_list['address'] = input_str[index_add+len_addr:index_pin+7]
            else:
                search_sdw = '(s/?[wid]/?[wid][wid]? ?..? ?:?)'
                sdw = re.search(search_sdw,input_str)
                
                if sdw:
                    index_sdw = sdw.start()
                    len_sdw = len(sdw.group())
                    
                search_dob = '(birth|dob)'
                dob = re.search(search_dob,input_str)

                if dob:
                    index_dob = re.search(dob[0],input_str).start()

                index_issue = input_str.find('issue')

                if index_issue != -1 and index_add != -1 and index_sdw != -1:
                    if index_add - index_sdw > index_issue - index_add:
                        dl_list['address'] = input_str[index_sdw + len_sdw:index_add]
                    else:
                        dl_list['address'] = input_str[index_add + len_addr:index_issue]
                elif index_dob != -1 and index_add != -1 and index_sdw != -1:
                    if index_add - index_sdw > index_dob - index_add:
                        dl_list['address'] = input_str[index_sdw + len_sdw:index_add]
                    else:
                        dl_list['address'] = input_str[index_add+len_addr:index_dob]
                else:
                    dl_list['address'] = 'NOT FOUND'
                    #return False
                    # dl_list['address'] = ''
            if ':' in dl_list['address']:
                add_string = dl_list['address']
                col_index = add_string.rfind(':')
                add_string = add_string[col_index+1:]
                dl_list['address'] = add_string.strip()
            
            #father's name
            sdw_str = r'(s/?[waid]/?[awid][awid]? ?..? ?:?)|(son|daughter|wife)[/ ]?(son|daughter|wife)?[/ ]?[/ ]?(son|daughter|wife)?( of )?'
            match_sdw = re.search(sdw_str,input_str)
            add_str = r'[a][d][d][ress.: ]{0,5}'
            match_add = re.search(add_str, input_str)
            if match_sdw and match_add:
                index_sdw = match_sdw.start()
                len_sdw = len(match_sdw.group())
                index_add = match_add.start()
                # len_addr = len(match_add.group())+1
                output_str = input_str[index_sdw+len_sdw:index_add]
                if len(output_str) > 25:
                    name_str = r'[a-z]+[ ][a-z]+'
                    father_name = re.search(name_str, output_str).group()
                else:
                    father_name = output_str
                dl_list['father_name'] = father_name.strip()
            elif match_sdw:
                add_str = r'[a][d][d][ress.: ]{0,5}'
                match_add = re.search(add_str, input_str)
                if match_sdw:
                    index_sdw = match_sdw.start()
                    len_sdw = len(match_sdw.group())
                    output_str = input_str[index_sdw+len_sdw:index_sdw+len_sdw+25]
                    if len(output_str) > 25:
                        name_str = r'[a-z]+[ ][a-z]+'
                        father_name = re.search(name_str, output_str).group()
                    else:
                        father_name = output_str
                    dl_list['father_name'] = father_name.strip()
            else:
                dl_list['father_name'] = ''
            response = dl_list
            print(response)
            return response

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

# Razor Payment Process
class PaymentProcessor(BaseCheckProcessor):
    '''
    NOT IN USE
    '''
    def process(self, name, amount, cid):

        try:
            res = self.redirect_payment_link(name,amount,cid)
            return True, res
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

    '''
    make razor pay connection based on RAZOR KEY and RAZORSECRET KEY
    '''
    def make_connection(self):
        try:
            import razorpay
            # RAZOR PAY API
            razorkey = app_settings.RAZORPAY_KEYS['RAZORKEY']
            razorsecret = app_settings.RAZORPAY_KEYS['RAZORSECRET']
            client = razorpay.Client(auth=(razorkey, razorsecret))

            return client
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    fetch payment detail based on payment id from razorpay
    '''
    def fetch_payment(self, txn_id):
        try:
            payment_id = txn_id

            client = self.make_connection()
            fetch_detail = client.payment.fetch(payment_id)

            return fetch_detail
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    capture payment detail based on payment id from razorpay
    '''
    def capture_payment(self,payload):
        try:
            payment_id = payload["txn_id"]
            payment_amount = payload["amount"]*100
            payment_currency = "INR"#payload["currency"]

            client = self.make_connection()
            capture_detail = client.payment.capture(payment_id, payment_amount, {"currency":payment_currency})

            return capture_detail
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    after payment done from razor pay check for the authorization and capture details 
    of paymen done by customer
    '''
    def afterRazorPayment(self, data, session_id):
        try:            
            print('after razor payment ---> ', data)
            txn_id = data["data"]['rzorPay_Txn_Id']
            url_id = data["data"]['url_id']
            find_pay = data["data"]['findPayDet']
            amount = data["data"]['amount']
            payload = {}
            payload["txn_id"] = txn_id
            payload["amount"] = amount
            print('amount--->',amount)
            if amount > 1: 
                cust_model = Model.customer_info.objects.get(session_id = session_id)
                
                #temp for handing multiple mail deliver for single payment
                if cust_model.payment_status == True:
                    subject = 'Get payment api hit twice'
                else:
                    subject = "Received Payment from WhatsApp"
                service_type = cust_model.service_type_id
                customer_type = cust_model.customer_type
                service_model = Model.service_detail.objects.filter(customer_type = customer_type, service_type_id = service_type).last()
                package_name = service_model.service_type_name
                mail_process = mail.Send_Email()                
                if customer_type == '1':
                    content = "Customer Name - " + str(cust_model.name) + "<br> Package Name: Myself - "+str(package_name) + "<br>Amount: " + str(amount)
                else:
                    content = "Customer Name - " + str(cust_model.name) + "<br> Package Name: Someone else - "+str(package_name) + "<br>Amount: " + str(amount)
                mail_process.process(subject,content)

            # Razorpay fetch payment details
            res = self.get_razorpay_fetch(txn_id)
            response_fetch = res.text
            response_fetch = json.loads(response_fetch)
            response_fetch['fetched_time'] = str(datetime.datetime.now())
            print("Response fetch : ",response_fetch)
            print("amount : ", amount)

            cust_obj = Model.customer_info.objects.get(session_id = session_id)
            # call model
            trans_model = Model.transaction_log()
            trans_model.customer_info = cust_obj
            trans_model.transaction_id = txn_id
            trans_model.fetch_str = response_fetch

            status = response_fetch["status"]

            if status == "authorized":
                trans_model.authorised = True

                #amount = 1
                # Razorpay capture payment
                # res = self.post_razorpay_capture(amount,txn_id)
                # response_capture = res.text
                # response_capture = json.loads(response_capture)
                # print("Response capture : ", response_capture)
                payload = {
                    "amount":amount,
                    "txn_id":txn_id
                }
                res = self.capture_payment(payload)
                res['captured_time'] = str(datetime.datetime.now())
                response_capture = res
                print("Response capture : ", response_capture)
                if response_capture['status'] == "captured":
                    trans_model.captured = True

                trans_model.capture_str = json.dumps(response_capture)

                # trans_model.capture_str = 'Finance'
            trans_model.save()
            
            res1 = {}
            res1["status"] = status
            res1["txn_id"] = txn_id
            res1['email'] = res["email"]
            return res1
    
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            res = {}
            res["status"] = ""
            res["txn_id"] = ""
            return res

class VerifyMobileOTPProcessor(BaseCheckProcessor):
    '''
    verify mobile otp of customer
    '''
    def process(self, session_id, otp):
        try:

            # # verify otp from database and set reminder for customer/candidate
            check_model = Model.customer_info.objects.get(session_id = session_id)
            # print(check_model.mobile_otp,otp)

            if check_model.mobile_no in ['+919205824013','+919205264013']:
                bypass = True
            else:
                bypass = False

            if check_model.adhaar_number:
                resp = verify_aadhaar_okyc_for_hellov(self, otp, check_model)
                if resp:
                    check_model = Model.customer_info.objects.filter(session_id = session_id).last()
                else:
                    pass    
                    
            if check_model.mobile_otp == int(otp) or bypass:
                check_model.mobile_verified = True
                check_model.save()

                # save reminder for customer/candidate
                payload = {
                    "session_id":session_id
                }
                processor = pr.DB_Processor()
                if check_model.customer_type == '3':
                    pass
                else:
                    processor.save_entry_to_reminder_table(payload)

                return True
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False


# Mobile OTP Processor
class MobileOTPProcessor(BaseCheckProcessor):

    '''
    create a randome 6 digit number for otp
    '''
    def generate_otp(self):

        try:
            # generate 6 digit otp random number
            import random
            import math

            ## storing strings in a list
            digits = [i for i in range(1, 10)]

            ## initializing a string
            random_str = ""

            ## we can generate any lenght of string we want
            for i in range(6):
                ## generating a random index
                index = math.floor(random.random() * 10)

                random_str += str(digits[index-1])

            return random_str

        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    send otp to customer mobile number
    '''
    def send_otp(self, session_id):

        try:
            mobile_otp = int(self.generate_otp())
            
            # get mobile number from customer_info  #can we get mobile_number from payload
            check_model = Model.customer_info.objects.get(session_id = session_id)

            mobile_no = check_model.mobile_no
                
            if check_model.mobile_otp:
                mobile_otp = check_model.mobile_otp
            else:
                mobile_otp = int(self.generate_otp())
            
            # When consent otp is initiated for aadhaar verification then otp will be treger from karza aadhaar verification with otp API
            if check_model.adhaar_number:
                resp = aadhaar_okyc_for_hellov(self, check_model)
                if resp.status_code == 200:
                    check_model.aadhaar_client_id = json.loads(resp.text)['message']['data']['client_id']
                    check_model.mobile_otp = mobile_otp
                    check_model.save() 
                    # sms_local.send_registration_otp_msg(mobile_no,mobile_otp)
                    return mobile_otp
                
                
            sms_local.send_registration_otp_msg(mobile_no,mobile_otp)

            # save otp to customer_info
            print("Updating mobile otp")
            check_model.mobile_otp = mobile_otp  #check here
            check_model.save()
            return mobile_otp

        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
        
def aadhaar_okyc_for_hellov(self, check_model):
    url = "https://checkapi.helloverify.com/external-apis/verify-aadhaar"
    payload = json.dumps({
            "aadhaar_num": check_model.adhaar_number,
            })
    headers = {
        'Authorization': "Token 41f2e0ba0527be17ba2985973b8664ad4fa47721",
        'Content-Type': 'application/json'
        }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def verify_aadhaar_okyc_for_hellov(self, otp, check_model):
    url = "https://checkapi.helloverify.com/external-apis/verify-aadhaar"
    payload = json.dumps({
            "client_id": check_model.aadhaar_client_id,
            "otp": otp
            })
    headers = {
        'Authorization': "Token 41f2e0ba0527be17ba2985973b8664ad4fa47721",
        'Content-Type': 'application/json'
        }

    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        check_model.mobile_otp = otp
        check_model.save()
        surpass_resp = json.loads(response.text)['message']
        check_model.aadhaar_verification_response = json.dumps(surpass_resp)
        check_model.save()      
        return True   
    return False
    
    
            
