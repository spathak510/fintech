from requests import api
from requests.sessions import session
from twilio.rest import Client
from hv_whatsapp_api import models as Model, views
from hv_whatsapp_api import views as main_view
from .Redis_Processor import RedisDB
from .views import Views
from .google_vision import Image_to_Ocr_text
from fuzzywuzzy import fuzz
from hv_whatsapp import settings as app_settings
import requests
from . import processor
import secrets
import json
from datetime import datetime, timedelta
from. import send_mail as mail
import logging
import inspect
import traceback
import numpy as np
import cv2, os
import requests
import json
import time
from requests.exceptions import ConnectTimeout
from local_stores.utils import validate_redeempin_for_strors, validate_redeempin_for_partners


logging.basicConfig(filename="error_log.log")
class Whatsapp_backend():
    redis_db = RedisDB()
    # redis_db.sql_query()
    api_call = Views()

    def __init__(self):
        pass

    def compare_fuzz(self, val1, val2):
        try:
            match1 = fuzz.ratio(val1, val2)
            match2 = fuzz.partial_ratio(val1, val2)
            match3 = fuzz.token_sort_ratio(val1, val2)
            match_percentage = max(match1, match2, match3)
            #print'match_percentage->', match_percentage)
            return match_percentage
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    # def skip_after_payment_input(self, payload, req_data):
    #     try:
    #         skip_input = False
    #         cust_obj = payload['cust_obj']
    #         session_id = payload['session_id']
    #         consent_count = Model.consent.objects.filter(order__customer_info = session_id).count()            
          
    #         if cust_obj.customer_type != '3' and req_data == '1':
    #             report_obj = Model.report_check.objects.filter(order__customer_info = session_id).last()
    #             if report_obj and report_obj.session_active == False:
    #                 report_obj.session_active = True
    #                 report_obj.save()
    #             elif not report_obj:
    #                 order_obj = Model.order.objects.filter(customer_info = session_id).last()
    #                 if order_obj and order_obj.send_incomplete_report == False:
    #                     main_view.generate_incomplete_report('', session_id)
    #             skip_input = True
    #         elif consent_count == 2 or cust_obj.customer_type != '3':
    #             skip_input = True
    #         return skip_input
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())

    # insert and update the data in DB and Redis
    def save_mobile_session(self,payload): # 1
        try:
            if "update" in payload: # for coupon issue handling
                in_mob_sess = Model.session_map.objects.filter(mobile_no = payload['mobile_no']).last()
                in_mob_sess.customer_info = payload['cust_obj']
                in_mob_sess.save()
                return True
            if "mobile_no" in payload and "session_id" in payload:
                # print('check1')
                mobile_no = payload["mobile_no"]
                session_id = payload["session_id"]
                if 'service_type_id' in payload:
                    service_type_id = payload["service_type_id"]
                # Check customer register table 
                in_cust_reg = Model.customer_register.objects.filter(mobile_no = mobile_no).exists()
                if in_cust_reg:
                    pass
                else:
                    # mail_process = mail.Send_Email()
                    # subject = "New Customer Registered"
                    # content = 'New Customer Registered with mobile number: ' + mobile_no
                    # mail_process.process(subject,content)
                    cust_reg = Model.customer_register()
                    cust_reg.mobile_no = mobile_no 
                    cust_reg.save()
                # check mobile session mapping table
                in_mob_sess = Model.session_map.objects.filter(mobile_no = mobile_no).exists()
                lookup_obj = Model.customer_lookup.objects.filter(customer_info = session_id).last()
                if in_mob_sess:# and 'getpay' not in payload:
                    mob_sess = Model.session_map.objects.filter(mobile_no = mobile_no).last()
                    mob_sess.customer_info = payload["cust_obj"]
                    # mob_sess.url_id = None
                    #if someoneelse scenario then save service_type_id from lookup table
                    if lookup_obj:
                        mob_sess.service_type_id = lookup_obj.service_type_id    
                    else:
                        mob_sess.service_type_id = service_type_id
                    mob_sess.save()
                    # update in redis
                    # self.redis_db.insert_update_session_map(payload)
                else:
                    mob_sess = Model.session_map()
                    mob_sess.mobile_no = mobile_no
                    mob_sess.customer_info = payload["cust_obj"]
                    if 'service_type_id' in payload:
                        mob_sess.service_type_id = service_type_id
                    mob_sess.save() #customer_info
                    # save in redis
                    # self.redis_db.insert_update_session_map(payload)
                # add new entry in customer session information table on hvstart
                # if lookup_obj:
                #     pass
                # else:
                #     cust_sess = Model.customer_info()
                #     cust_sess.mobile_no = mobile_no
                #     cust_sess.session_id = session_id
                #     cust_sess.save()
                payload['results'] = 'correct_input'
                return payload
            else:
                payload['results'] = 'incorrect_input'
                return payload
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload

    # get session id from mobile number from Redis
    def get_session_id(self,payload): # 2 - correct
        
        try:

            mobile_no = payload["mobile_no"]

            sts, res = self.redis_db.get_session_id_from_redis(mobile_no)

            if sts:
                session_id = res["session_id"]
                return session_id
            else:
                return ''
    
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # get action on question from redis
    def get_action_on_ques(self,payload): # 3

        try:
            sts, res = self.redis_db.get_action_on_ques_from_redis(payload)

            if sts:
                action_enum = res["action_on_ques"]
                return action_enum
            else:
                return ''
        
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # find next question from Redis
    def get_next_ques(self,payload):

        try:
            sts, res = self.redis_db.get_next_question_from_redis(payload)
            if '?Tip' in res['question_desc'] or '?टिप' in res['question_desc']:
                res['question_desc'] = res['question_desc'].replace('?Tip', '💡Tip').replace('?टिप', '💡टिप')
            if '{_' in res['question_desc']:
                # payload = {'question_desc': res['question_desc'], 'customer_type': payload['customer_type'], 'session_id': payload['session_id'], 'mobile_no': payload['mobile_no']}
                payload['question_desc'] = res['question_desc']
                ques = (payload['question_desc']).lower()
                if 'make the payment' in ques and payload['user_action'] == 1:
                    payload['service_type_id'] = 1
                res['question_desc'] = self.generate_dynamic_ques(payload)
            return res
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # get latest(last) session log detail for session id
    def get_session_data(self, payload):

        try:

            session_id = payload["session_id"]

            sess_log = Model.session_log.objects.get(customer_info = session_id)

            sess_data = {}
            sess_data["session_id"] = session_id
            sess_data["prev_question_id"] = sess_log.prev_question_id
            sess_data["service_type_id"] = sess_log.service_type_id
            sess_data["id_type"] = sess_log.id_type
            sess_data["customer_type"] = sess_log.customer_type
            sess_data["language_type"] = sess_log.language_type
            sess_data["mobile_no"] = sess_log.mobile_no
            sess_data['cust_obj'] = payload['cust_obj']

            return sess_data
        
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # save after completion of every operation of a session
    def save_session_log(self,payload):

        try:
            if "session_id" in payload:
                sess_log = Model.session_log.objects.filter(customer_info = payload['session_id']).last()
                if sess_log:
                    pass
                else:
                    sess_log = Model.session_log()

                sess_log.customer_info = payload["cust_obj"]

                if "mobile_no" in payload:
                    sess_log.mobile_no = payload["mobile_no"]
                if "prev_question_id" in payload:
                    sess_log.prev_question_id = payload["prev_question_id"]
                if "user_action" in payload:
                    sess_log.user_action = payload["user_action"]
                if "results" in payload:
                    sess_log.results = payload["results"]
                if "new_customer_type" in payload:
                    sess_log.customer_type = payload["new_customer_type"]
                elif "customer_type" in payload:
                    sess_log.customer_type = payload["customer_type"]
                if "language_type" in payload:
                    sess_log.language_type = payload["language_type"]
                if "service_type_id" in payload:
                    sess_log.service_type_id = payload["service_type_id"]
                if "id_type" in payload:
                    sess_log.id_type = payload["id_type"]
                sess_log.save()
                return True            
            return False

        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    # save language_type to session_map, customer_info table
    def save_language_type(self,payload):

        try:

            session_id = payload["session_id"]
            language_type = payload["user_action"]
            cust_sess = Model.customer_info.objects.get(session_id = session_id)
            if cust_sess:                
                cust_sess.language_type = language_type
                cust_sess.save()
                payload["language_type"] = language_type
                payload["results"] = 'correct_input'
            else:
                payload["results"] = 'incorrect_input'
            return payload
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload


    # get service type id of customer bases on session id
    def get_service_type_id(self, payload):
        try:
            session_id = payload["session_id"]
            result = self.redis_db.get_data_by_session_id(session_id)
            service_type_id = result.service_type_id
            return service_type_id

        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return 'incorrect_input'

    
    # save service_type_id to session_log, customer_info (service_type_id instead of service_type)
    def save_service_type(self,payload):
        try:            
            payload["service_type_id"] = payload["user_action"]
            session_id = payload["session_id"]
            service_type_id = payload["service_type_id"] #service_type_id
            # check mobile session mapping table
            in_mob_sess = Model.session_map.objects.filter(customer_info = session_id).last()
            if in_mob_sess:
                in_mob_sess.service_type_id = service_type_id
                in_mob_sess.save()
            else:
                payload["results"] = 'incorrect_input'
                return payload

            payload["results"] = 'correct_input'
            # payload["service_type_id"] = service_type_id

            # check customer session information table
            cust_sess = Model.customer_info.objects.get(session_id = session_id)
            lookup_model = Model.customer_lookup.objects.filter(customer_info = session_id).last()
            
            if cust_sess:                
                if cust_sess.service_type_id == 2 and service_type_id == 1: #updating price on service switch
                    service_obj = Model.service_detail.objects.filter(service_type_id = 1, customer_type = cust_sess.customer_type).last()                    
                else:
                    service_obj = Model.service_detail.objects.filter(service_type_id = service_type_id, customer_type = cust_sess.customer_type).last()        
                if cust_sess.customer_type == '2' and lookup_model:
                    lookup_model.service_type_id = service_type_id
                    lookup_model.save()
                if cust_sess.service_type_id < 20:
                    cust_sess.final_price = int(service_obj.service_type_price)
                cust_sess.service_type_id = service_type_id
                cust_sess.save()
            else:
                payload["results"] = 'incorrect_input'
                return payload
            return payload
        
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload["results"] = 'incorrect_input'
            return payload

    # save id_type to mobile session mapping, customer_info tables
    def save_id_type(self,payload):
        try:
            # mobile session mapping, customer_info tables
            session_id = payload["session_id"]
            id_type = payload["user_action"]

            # check customer session information table
            cust_sess = Model.customer_info.objects.get(session_id = session_id)
            if cust_sess:                
                cust_sess.id_type = id_type
                cust_sess.save()
            else:
                payload['results'] = 'incorrect_input'
                return payload
            payload['id_type'] = id_type
            payload['results'] = 'correct_input'
            return payload
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload

    # save UAN number to customer_info
    def save_uan(self, payload):
        try:            
            session_id = payload["session_id"]

            #if user don't have uan
            if 'user_action' in payload and payload['user_action'] == 2:
                payload['results'] = 'correct_input'
                return payload
            if 'input_data' not in payload or len(payload["input_data"].strip()) != 12:
                payload['results'] = 'incorrect_input'
                return payload                        
            cust_sess = Model.customer_info.objects.get(session_id = session_id)                                    
            # check customer session information table
            
            cust_sess.uan = payload["input_data"]
            cust_sess.save()                
            
            payload['results'] = 'uan_correct'
            return payload
        except Exception as ex:            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload

    # Go to previous question getting from session_log table
    def go_to_previous_ques(self,payload):  #will check
        try:
            if payload['customer_type'] == '2' and payload['service_type_id'] == 0:
                session_id = payload["session_id"]
                mobile_no = payload['mobile_no']
                cust_reg = Model.customer_register.objects.get(mobile_no = mobile_no)
                cust_reg.customer_type = '1'
                cust_reg.save()
                
                cust_sess = Model.customer_info.objects.get(session_id = session_id)
                cust_sess.customer_type = '1'
                cust_sess.save()
                payload['customer_type'] = '1'
                payload['results'] = 'correct_input'
                return payload
            elif payload['service_type_id'] > 0:
                user_action = payload['user_action']
                service_type_id = payload['service_type_id']
                payload['user_action'] = 0
                payload = self.save_service_type(payload)
                payload['user_action'] = user_action
                payload['service_type_id'] = service_type_id
                return payload
            elif payload['user_action'] == 9:
                payload['results'] = 'correct_input'
                return payload
            else: 
                payload['results'] = 'incorrect_input'
                return payload
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # parse the front image uploaded by customer
    def parse_front_image(self,payload):

        try:

            session_id = payload["session_id"]
            image_url = payload["url"]
            id_type = payload['id_type']
            mobile_no = payload['mobile_no']
            pay_obj = processor.DB_Processor()
            cust_model = Model.customer_info.objects.get(session_id = session_id)
            language_type = cust_model.language_type
            if language_type == 1:
                pay_obj.create_thread(mobile_no, 'We are processing your request. \n*Please wait.*\n')
            elif language_type == 2:
                pay_obj.create_thread(mobile_no, 'हम आपके निवेदन पर कार्य कर रहे हैं। \n*कृपया प्रतीक्षा करें।*\n')
            image_url = requests.head(image_url, allow_redirects=True).url
            google_vision_api = Image_to_Ocr_text()
            ocr_string = google_vision_api.detect_text_uri(image_url)
            #print'ocr_string:',ocr_string)
            # if ocr_string == 'exception':

            in_ocr_model = Model.ocr_response.objects.filter(customer_info = session_id).exists()

            if in_ocr_model:
                check_model = Model.ocr_response.objects.get(customer_info = session_id)
                check_model.id_type = id_type
                check_model.front_image_url = image_url
                check_model.front_response_str = ocr_string
                check_model.save()
            else:
                check_model = Model.ocr_response()
                check_model.customer_info = payload["cust_obj"]
                check_model.id_type = id_type
                check_model.front_image_url = image_url
                check_model.front_response_str = ocr_string
                check_model.save()

            # Image parsing result
            new_payload = {
                "ocr_string":ocr_string,
                'session_id': session_id
            }

            if id_type == '1':
                # parse adhaar
                result = self.api_call.get_adhaar_front_results(new_payload)
                if result != False:
                    save_adhaar_data = Model.customer_info.objects.get(session_id = session_id)
                    if result['adhaar_number'] == '':
                        payload['results'] = 'blur_or_Incorrect_image'
                        return payload
                    save_adhaar_data.adhaar_number = (result['adhaar_number']).strip()
                    save_adhaar_data.dob = result['dob']
                    save_adhaar_data.gender = result['gender']
                    save_adhaar_data.name = result['name']
                    save_adhaar_data.save()
                    #SAVE AADHAAR RESULT
                    save_result = Model.ocr_response.objects.get(customer_info = session_id)
                    save_result.front_parse_result = json.dumps(result)
                    save_result.save()
                else:
                    payload['results'] = 'blur_or_Incorrect_image'
                    return payload  
            elif id_type == '2':
                # parse driving license
                result = self.api_call.get_dl_front_results(new_payload)
                if result != False:
                    save_dl_data = Model.customer_info.objects.get(session_id = session_id)
                    save_dl_data.address = result['address']
                    save_dl_data.dl_number = result['dl_number']
                    save_dl_data.dob = result['dob']
                    save_dl_data.father_name = result['father_name'] 
                    save_dl_data.name = result['name']                   
                    save_dl_data.save()
                    #save DL result
                    save_result = Model.ocr_response.objects.get(customer_info = session_id)
                    save_result.front_parse_result = json.dumps(result)
                    save_result.save()
                else:
                    payload['results'] = 'blur_or_Incorrect_image'
                    return payload
            if  id_type == '2' and len(result['address']) > 0:
                payload['results'] = 'correct_input'
            elif len(str(result)) > 40:
                payload['results'] = 'imageOk'
            else:
                payload['results'] = 'blur_or_Incorrect_image'
            #printpayload)
            return payload
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'blur_or_Incorrect_image'
            return payload

    # parse the back image uploaded by customer
    def parse_back_image(self,payload):

        try:
            session_id = payload["session_id"]
            id_type = payload['id_type']
            mobile_no = payload['mobile_no']
            get_dl_data = Model.customer_info.objects.get(session_id = session_id)
            if id_type == '2' and len(get_dl_data.address) != 0:
                payload['results'] = 'imageOk'
                return payload

            image_url = payload["url"]
            pay_obj = processor.DB_Processor()
            cust_model = Model.customer_info.objects.get(session_id = session_id)
            language_type = cust_model.language_type
            if language_type == 1:
                pay_obj.create_thread(mobile_no, 'We are processing your request. \n*Please wait.*\n')
            elif language_type == 2:
                pay_obj.create_thread(mobile_no, 'हम आपके निवेदन पर कार्य कर रहे हैं। \n*कृपया प्रतीक्षा करें।*\n')
            image_url = requests.head(image_url, allow_redirects=True).url
            google_vision_api = Image_to_Ocr_text()
            ocr_string = google_vision_api.detect_text_uri(image_url)

            in_ocr_model = Model.ocr_response.objects.filter(customer_info = session_id).exists()

            if in_ocr_model:
                check_model = Model.ocr_response.objects.get(customer_info = session_id)
                check_model.id_type = id_type
                check_model.back_image_url = image_url
                check_model.back_response_str = ocr_string
                check_model.save()
            else:
                check_model = Model.ocr_response()
                check_model.customer_info = payload["cust_obj"]
                check_model.id_type = id_type
                check_model.back_image_url = image_url
                check_model.back_response_str = ocr_string
                check_model.save()

            # Image parsing result
            new_payload = {
                "ocr_string":ocr_string,
                'session_id': session_id
            }

            if id_type == '1':
                # parse adhaar
                result = self.api_call.get_adhaar_back_results(new_payload)
                if result == 'mismatch':
                    payload['results'] = 'blur_or_Incorrect_image'
                    return payload
                if result != False:
                    save_adhaar_data = Model.customer_info.objects.get(session_id = session_id)
                    save_adhaar_data.address = result['address']    
                    save_adhaar_data.father_name = result['father_name']
                    save_adhaar_data.save()
                    save_result = Model.ocr_response.objects.get(customer_info = session_id)
                    save_result.back_parse_result = json.dumps(result)
                    save_result.save()
                else:
                    payload['results'] = 'blur_or_Incorrect_image'
                    return payload
            elif id_type == '2':
                # parse driving license
                result = self.api_call.get_dl_back_results(new_payload)
                if result != False:
                    save_dl_data = Model.customer_info.objects.get(session_id = session_id)
                    save_dl_data.address = result['address']
                    if len(save_dl_data.father_name) == 0 and result['father_name'] != '':
                        save_dl_data.father_name = result['father_name']
                    save_dl_data.save()
                    save_result = Model.ocr_response.objects.get(customer_info = session_id)
                    save_result.back_parse_result = json.dumps(result)
                    save_result.save()
                else:
                    payload['results'] = 'blur_or_Incorrect_image'
                    return payload
            # print('result back: ', result)
            if len(str(result)) > 40:
                payload['results'] = 'imageOk'
                return payload
            else:
                payload['results'] = 'blur_or_Incorrect_image'
                return payload
        except Exception as ex:            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'blur_or_Incorrect_image'
            return payload

    # save customer type in customer_register, session_map, customer_info table
    def save_customer_type(self, payload):
        try: 
            session_id = payload["session_id"]
            customer_type = payload["user_action"]
            mobile_no = payload["mobile_no"]
            # save in customer_register table
            cust_reg = Model.customer_register.objects.get(mobile_no = mobile_no)
            cust_reg.customer_type = customer_type
            cust_reg.save()
            # save in customer_info
            cust_sess = Model.customer_info.objects.get(session_id = session_id)
            # mob_obj = Model.session_map.objects.filter(customer_info = session_id).last()
            cust_sess.customer_type = customer_type
            cust_sess.save()
            payload['customer_type'] = str(customer_type)
            payload['results'] = 'correct_input'           
            return payload

        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload


    # save name in customer_info table
    def save_name(self, payload):
        try:

            session_id = payload["session_id"]
            name = ((payload["input_data"]).strip()).upper()
            mobile_no = payload["mobile_no"]

            # save in customer_info
            cust_sess = Model.customer_info.objects.get(session_id = session_id)
            cust_sess.name = name
            cust_sess.save()

            #save in customer_lookup
            cust_lookup = Model.customer_lookup.objects.filter(customer_info = session_id).last()
            if cust_lookup:
                cust_lookup.vendor_name = name
                cust_lookup.vendor_mobile = mobile_no
                cust_lookup.save()
            else:
                cust_lookup = Model.customer_lookup()
                cust_lookup.vendor_name = name
                cust_lookup.vendor_mobile = mobile_no
                cust_lookup.customer_info = payload['cust_obj']
                cust_lookup.vendor_id = session_id
                cust_lookup.save()
            
            payload['results'] = 'correct_input'
            # admin_payload = {'session_id': session_id, 'name': name}
            # # self.insert_update_admin_order_detail(admin_payload)
            # self.insert_update_admin_incomplete_trans(admin_payload)
            return payload
        
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload

    # check address similarity
    # def check_address_similarity(self,payload):
    #     try:

    #         claimed_address = payload["input_data"]
    #         cust_data = Model.customer_info.objects.filter(session_id = payload['session_id']).last()
    #         fuzz_val = app_settings.FUZZY_ADDRESS
    #         match_percentage = self.compare_fuzz(claimed_address.lower(), (cust_data.address).lower())
    #         cust_data.address_match_percentage = match_percentage
    #         if match_percentage >= fuzz_val:
    #             #saving address corrected by customer
    #             cust_data.address = claimed_address.upper()       
    #             if len(cust_data.father_name) != 0:
    #                 payload['results'] = 'address_allowed'
    #             else:
    #                 payload['results'] = 'father_name_not_found'
    #         else:
    #             payload['results'] = 'address_not_allowed'                
    #         cust_data.save()
    #         return payload
    #     except Exception as ex:
            
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         payload['results'] = 'incorrect_input'
    #         return payload
            

    # save address in customer_info table
    def save_address(self, payload):
        try:
            session_id = payload["session_id"]
            # save address in customer session information
            cust_sess = Model.customer_info.objects.get(session_id = session_id)
            if len(cust_sess.father_name) != 0:
                payload['results'] = 'father_name_found'
                return payload #father name exist
            else:
                payload['results'] = 'father_name_not_found'
                return payload
        
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload


    # save father name in customer_info table
    def save_father_name(self, payload):
        try:
            if payload['customer_type'] == '3' or payload['user_action'] == 1:
                payload['results'] = 'correct_input'
                return payload
            if payload['service_type_id'] == 1: 
                cust_sess = Model.customer_info.objects.get(session_id = payload['session_id'])
                cust_sess.father_name = payload['input_data']
                cust_sess.save()
                payload['results'] = 'correct_input'
                return payload
            elif payload['service_type_id'] == 2:
                cust_sess = Model.customer_info.objects.get(session_id = payload['session_id'])
                cust_sess.father_name = payload['input_data']
                cust_sess.save()
                payload['results'] = 'correct_input'
                return payload
            else:
                payload['results'] = 'incorrect_input'
                return payload
        
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload

    # get payment status from table
    def get_payment_status(self, payload):
        try:
            session_id = payload["session_id"]

            # get paymaent status from Customer session Information table
            cust_sess = Model.customer_info.objects.get(session_id = session_id)
            payment_status = cust_sess.payment_status
            if payment_status == True:
                payload['results'] = 'payment_success'
                return payload
            else:
                payload['results'] = 'payment_fail'
                return payload

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload     

    # save candidate mobile number in Customer Session Information table
    def save_candidate_mobile(self, payload):
        try:
            session_id = payload["session_id"]
            service_type_id = payload["service_type_id"]
            payload["input_data"] = (payload["input_data"]).replace('<', '').replace('>', '')
            data = payload["input_data"].split(',')
            if len(data) == 2:
                candidate_mobile = '+91' + data[1].strip()
                candidate_name = (data[0].strip()).upper()
                if len(candidate_mobile) != 13: #validating mobile number
                    payload['results'] = 'incorrect_input'
                    return payload
            else:
                payload['results'] = 'incorrect_input'
                return payload
            # get paymaent status from Customer session Information table
            cust_lookup = Model.customer_lookup.objects.get(customer_info = session_id)
            cust_lookup.candidate_mobile = candidate_mobile
            cust_lookup.candidate_name = candidate_name
            cust_lookup.service_type_id = service_type_id
            cust_lookup.save()
            payload['results'] = 'correct_input'
            return payload

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload

    # save consent in consent
    def save_consent(self, payload):
        try:
            session_id = payload["session_id"]
            candidate_mobile = payload["candidate_mobile"]

            # get paymaent status from Customer session Information table
            cust_sess = Model.customer_info.objects.get(session_id = session_id)
            cust_sess.candidate_mobile = candidate_mobile
            cust_sess.save()
            payload['results'] = 'correct_input'
            return payload

        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload

    '''
    generate dynamic questions if applicable
    '''
    def generate_dynamic_ques(self, payload):
        try:
            
            #print'from dynamic ques-->',payload)
            cust_obj = Model.customer_info.objects.get(session_id = payload['session_id'])
            map_obj = Model.customer_lookup.objects.filter(customer_info = payload['session_id']).last()
            mob_obj = Model.session_map.objects.filter(customer_info = payload['session_id']).last()
            language = cust_obj.language_type
            if cust_obj:
                language_type = cust_obj.language_type
                if '{_requester_}' in payload['question_desc']:
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_requester_}', (((map_obj.vendor_name).strip())).upper()) 
                if '{_candidate_}' in payload['question_desc']:
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_candidate_}', (((map_obj.candidate_name).strip())).upper())
                # if '{_dis_price_}' in payload['question_desc']:
                #     service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = payload['service_type_id']).last()
                #     ques = payload['question_desc']
                #     payload['question_desc'] = ques.replace('{_dis_price_}', str(service_obj.service_type_price - service_obj.service_type_discount))
                if '{_service_name_}' in payload['question_desc']:
                    try:
                        service_type_id = payload['service_type_id']
                    except:
                        service_type_id = self.get_service_type_id(payload) #get current service_type_id
                    if not service_type_id or service_type_id == 20:
                        service_type_id = self.get_service_type_id(payload) #get current service_type_id
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = service_type_id).last()
                    ques = payload['question_desc']
                    if language_type == 1:
                        service_name = (service_obj.service_type_name).split('-')
                        first = '*'+service_name[0].strip()+'*'
                        second = ('\n'+(service_name[1]).strip()).replace('.','')
                    else:
                        service_name = (service_obj.service_type_name_hindi).split('-')
                        first = '*'+service_name[0].strip()+'*'
                        second = '\n'+(service_name[1]).strip()
                    service_name = first + second
                    #printservice_name)
                    payload['question_desc'] = ques.replace('{_service_name_}', service_name).replace('। को', '')
                if '{_attempt_}' in payload['question_desc']:
                    coupon_obj = Model.customer_coupon_code.objects.filter(mobile_no = payload['mobile_no']).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_attempt_}', str(coupon_obj.allowed_attempt))
                    if coupon_obj.allowed_attempt == 1:
                        payload['question_desc'] = payload['question_desc'].replace('attempts', 'attempt')
                if '{_hours_}' in payload['question_desc']:
                    coupon_obj = Model.customer_coupon_code.objects.filter(mobile_no = payload['mobile_no']).last()
                    ques = payload['question_desc']
                    last_attempt = coupon_obj.last_attempt_time.replace(tzinfo=None)
                    current_attempt = datetime.now().replace(tzinfo=None)
                    time_diff = (current_attempt - last_attempt)
                    total_seconds = time_diff.total_seconds()
                    minutes = total_seconds/60
                    hours = 24 - int(minutes/60)
                    payload['question_desc'] = ques.replace('{_hours_}', str(hours))
                if '{_attempt_promo_}' in payload['question_desc']:
                    promocode_obj = Model.customer_promocode.objects.filter(mobile_no = payload['mobile_no']).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_attempt_promo_}', str(promocode_obj.allowed_attempt))
                    if promocode_obj.allowed_attempt == 1:
                        payload['question_desc'] = payload['question_desc'].replace('attempts', 'attempt')
                if '{_hours_promo_}' in payload['question_desc']:
                    promocode_obj = Model.customer_promocode.objects.filter(mobile_no = payload['mobile_no']).last()
                    ques = payload['question_desc']
                    last_attempt = promocode_obj.last_attempt_time.replace(tzinfo=None)
                    current_attempt = datetime.now().replace(tzinfo=None)
                    time_diff = (current_attempt - last_attempt)
                    total_seconds = time_diff.total_seconds()
                    minutes = total_seconds/60
                    hours = 24 - int(minutes/60)
                    payload['question_desc'] = ques.replace('{_hours_promo_}', str(hours))
                if '{_final_price_}' in payload['question_desc']:
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = service_type_id).last()
                    ques = payload['question_desc']
                    if language_type == 1:
                        payload['question_desc'] = ques.replace('{_final_price_}', (str(int(cust_obj.final_price)) + '.'))
                    else:
                        payload['question_desc'] = ques.replace('{_final_price_}', str(int(cust_obj.final_price)))
                if '{_price1_}' in payload['question_desc']:
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = 1).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_price1_}', str(int(service_obj.service_type_price)))
                if '{_price2_}' in payload['question_desc']:
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = 2).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_price2_}', str(int(service_obj.service_type_price)))
                if '{_price3_}' in payload['question_desc']:
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = 3).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_price3_}', str(int(service_obj.service_type_price)))
                if '{_price4_}' in payload['question_desc']:
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = 4).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_price4_}', str(int(service_obj.service_type_price)))
                if '{_price5_}' in payload['question_desc']:
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = 5).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_price5_}', str(int(service_obj.service_type_price)))
                if '{_price6_}' in payload['question_desc']:
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = 6).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_price6_}', str(int(service_obj.service_type_price)))
                if '{_price7_}' in payload['question_desc']:
                    service_obj = Model.service_detail.objects.filter(customer_type = payload['customer_type'], service_type_id = 7).last()
                    ques = payload['question_desc']
                    payload['question_desc'] = ques.replace('{_price7_}', str(int(service_obj.service_type_price)))    
                if '{_url_}' in payload['question_desc']:
                    ques = payload['question_desc']
                    url_id = secrets.token_urlsafe(6)
                    mob_obj.url_id = url_id
                    #print"Vendor URl:",url_id)
                    mob_obj.save()
                    if app_settings.LOCAL_ENV == False:
                        payload['question_desc'] = ques.replace('{_url_}', 'https://hellov.in/app/?sid='+url_id)
                    else:
                        payload['question_desc'] = ques.replace('{_url_}', 'http://c063a147caa9.ngrok.io/?sid='+url_id)
                    # admin_payload = {'session_id': payload['session_id'], 'link_status': 'link_status'}
                    # self.insert_update_admin_incomplete_trans(admin_payload)

                    # url status in url_expiry model
                    url_expire_model = Model.url_expiry()
                    url_expire_model.customer_info = payload['cust_obj']
                    url_expire_model.url_id = url_id
                    url_expire_model.url_send_time = datetime.now()
                    url_expire_model.save()
                    
                if '{_conurl_}' in payload['question_desc']:
                    ques = payload['question_desc']
                    url_id = secrets.token_urlsafe(6)
                    mob_obj.url_id = url_id
                    #print"Candidate URl:",url_id)
                    mob_obj.save()
                    if app_settings.LOCAL_ENV == False:
                        payload['question_desc'] = ques.replace('{_conurl_}', 'https://hellov.in/app/?sid='+url_id)
                    else:
                        payload['question_desc'] = ques.replace('{_conurl_}', 'http://c063a147caa9.ngrok.io/?sid='+url_id)
                    # url status in url_expiry model
                    url_expire_model = Model.url_expiry()
                    url_expire_model.customer_info = payload['cust_obj']
                    url_expire_model.url_id = url_id
                    url_expire_model.url_send_time = datetime.now()
                    url_expire_model.save()
                if '{_document_}' in payload['question_desc']:
                    ques = payload['question_desc']
                    if language_type == 1:
                        if cust_obj.id_type == '1':
                            payload['question_desc'] = ques.replace('{_document_}', 'AADHAAR')
                        elif cust_obj.id_type == '2':
                            payload['question_desc'] = ques.replace('{_document_}', 'DRIVING LICENCE')
                    else:
                        if cust_obj.id_type == '1':
                            payload['question_desc'] = ques.replace('{_document_}', 'आधार कार्ड')
                        elif cust_obj.id_type == '2':
                            payload['question_desc'] = ques.replace('{_document_}', 'ड्राइविंग लाइसेंस')
                dynamic_ques = payload['question_desc']
          
                return dynamic_ques
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ''

    '''
    NOT IN USE
    '''
    def ask_correct_fathername(self, payload):
        try:
            
            if payload['user_action'] == 2:
                payload['results'] = 'correct_input'
                return payload
            else:
                payload['results'] = 'incorrect_input'
                return payload

        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload

    '''
    NOT IN USE
    '''
    def ask_correct_address(self, payload):
        try:
            
            if payload['user_action'] == 2:
                payload['results'] = 'correct_input'
                return payload
            else:
                payload['results'] = 'incorrect_input'
                return payload

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload
    
    #check every input validity
    def is_valid_input(self,payload):
        try:
            status = self.redis_db.is_valid_from_redis(payload)
            
            return status
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False


    #create orders
    def create_order(self, payload):
        try:
            order_id = ""
            session_id = payload['session_id']
            transaction_id = payload['txn_id']
            
            cust_obj = Model.customer_info.objects.get(session_id = session_id)
            if cust_obj.payment_status == 1:
                customer_name = cust_obj.name.lower().replace(" ", "_")
                order_id = (secrets.token_hex(3)).upper()+str(session_id)
                # order_id = customer_name+"_"+order_id
                order_id = order_id
                order_obj = Model.order()
                order_obj.customer_info = cust_obj
                order_obj.order_id = order_id
                order_obj.name = cust_obj.name
                order_obj.mobile_no = cust_obj.mobile_no
                # order_obj.customer_type = cust_obj.customer_type
                # order_obj.service_type_id = cust_obj.service_type_id
                order_obj.price = Model.service_detail.objects.filter(customer_type= cust_obj.customer_type , service_type_id = cust_obj.service_type_id).last().service_type_price
                order_obj.transaction_id = transaction_id 
                order_obj.save()
                
                # deleting entry from reminder table
                Model.reminder.objects.filter(customer_info = session_id).delete()

                #creating new entry in api_hit_count table
                api_hit_obj = Model.api_hit_count()
                api_hit_obj.order = order_obj
                api_hit_obj.save()
            # set initial values in session_map
            cust_lookup = Model.customer_lookup.objects.filter(customer_info = session_id).last()
            if cust_lookup:
                candidate_mobile = cust_lookup.candidate_mobile                              

                # create new entry in customer_info table
                cand_obj = Model.customer_info()
                cand_obj.mobile_no = candidate_mobile
                cand_obj.customer_type = '3'
                cand_obj.name = cust_lookup.candidate_name
                cand_obj.service_type_id = cust_lookup.service_type_id
                cand_obj.uan = cust_obj.uan
                cand_obj.promo_applied = cust_obj.promo_applied
                cand_obj.final_price = cust_obj.final_price
                cand_obj.payment_status = 1
                cand_obj.save()

                # updating customer_info of order table for someoneelse
                order_obj = Model.order.objects.get(order_id = order_id)
                order_obj.customer_info = cand_obj
                order_obj.save()
                
                #updating lookup model session_id
                cust_lookup.customer_info = cand_obj
                cust_lookup.save()

                # updating session_map table
                ms_obj = Model.session_map.objects.get(customer_info = session_id)
                ms_obj.mobile_no = candidate_mobile
                ms_obj.customer_info = cand_obj
                ms_obj.save()
                
                # save session log to continue the flow
                sess_obj = Model.session_log.objects.get(customer_info = session_id)
                sess_obj.customer_info = cand_obj
                sess_obj.customer_type = '3'
                sess_obj.mobile_no = candidate_mobile
                sess_obj.prev_question_id = 60  #try to handle this some other way
                sess_obj.save()

                session_id = cand_obj.session_id
            
            if cust_lookup == None:
                # if cand_obj.mobile_no not in ['+9181307335051','+9198990117421','+9192052640131']:
                self.set_checks(payload)
            return order_id, session_id
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ""        

    # set checks status in report_check table
    def set_checks(self,payload):

        try:
            session_id = payload["session_id"]

            cust_model = Model.customer_info.objects.get(session_id = session_id)
            if cust_model.adhaar_number == '244340560639' and cust_model.customer_type == '1':
                from .views import Views
                report_ins = Views()
                report_ins.send_demo_report(4873)
            if cust_model.dl_number == 'rj2720090142779' and cust_model.customer_type == '1':
                from .views import Views
                report_ins = Views()
                report_ins.send_demo_report(11640)
            payment_status = cust_model.payment_status
            customer_type = cust_model.customer_type
            service_type_id = cust_model.service_type_id
            order_obj = Model.order.objects.get(customer_info=session_id)

            # get checks detail from service type
            service_model = Model.service_detail.objects.filter(customer_type = customer_type, service_type_id=service_type_id).last()
            check_name = Model.check_types(service_model.check_types).name

            if payment_status:
                report_model = Model.report_check()
                report_model.order = order_obj
                report_model.report_status = '0' #pending

                if "id" in check_name:
                    report_model.id_check_status = False
                if "crime" in check_name:
                    report_model.crime_check_status = False
                if "emp" in check_name:
                    report_model.emp_check_status = False
                if "kyc" in check_name:
                    report_model.id_check_status = False

                report_model.send_report = False
                report_model.save()
            
            ocr_obj = Model.ocr_response.objects.get(customer_info=session_id)
            subject = "Report Check Created"
            content = f'''Report checks created for session_id: {session_id} \
<br><br><br>Please check below IDs for your reference:<br><br> \
Front Image URL:<br> {ocr_obj.front_image_url} <br>Back Image URL:<br> \
{ocr_obj.back_image_url}'''
            mail_process = mail.Send_Email()
            mail_process.process(subject,content)  
            return True

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


    '''
    call all the api's required for the case
    '''
    def karza_api_call(self, payload):
        try:
            # self.admin_view_panel(payload)
            self.myview = Views()
            session_id = payload['session_id']
            cust_obj = Model.customer_info.objects.get(session_id = session_id)
            mobile_no = cust_obj.mobile_no
            if cust_obj.service_type_id == 2:
                self.myview.get_uan_results(payload)
            if cust_obj.id_type == '1':
                self.myview.get_adhaar_results(payload) 
            elif cust_obj.id_type == '2':
                self.myview.get_dl_results(payload)     
            self.myview.get_crimecheck_results(payload)
            #print'karza processing done')
            order_obj = Model.order.objects.get(customer_info = session_id)
            order_id = order_obj.order_id
            payload['order_id'] = order_id

            return True
        except Exception as ex:
            
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False      

    # Insert update Admin Order Details view
    # def insert_update_admin_order_detail_status(self,payload):
    #     try:

    #         session_id = payload['session_id']
    #         order_id = payload['order_id']
    #         # model objects
    #         order_model = Model.order.objects.filter(customer_info = session_id).last()
    #         dl_model = Model.dl_manual_response.objects.filter(order = order_id).exists()
    #         crime_model = Model.criminal_result.objects.filter(order = order_id).last()
    #         # save details in Admin Model
    #         admin_model = Model.AdminOrderModel.objects.filter(order_id = order_id).last()
    #         admin_model.cust_model = payload['cust_obj']
    #         admin_model.order = order_model
    #         if dl_model and crime_model and crime_model.manual_color_code != '0':
    #             admin_model.auto_or_manual = 'Manual_DL, Manual_Crime'
    #         elif dl_model:
    #             admin_model.auto_or_manual = 'Manual_DL'
    #         elif crime_model and crime_model.manual_color_code != '0':
    #             admin_model.auto_or_manual = 'Manual_Crime'
    #         else:
    #             admin_model.auto_or_manual = 'Auto'
    #         if crime_model and (crime_model.manual_color_code == '1' or crime_model.manual_color_code == '0'):
    #             admin_model.final_status = 'Green'
    #         elif crime_model and crime_model.manual_color_code == '2':
    #             admin_model.final_status = 'Red'
    #         else:
    #             admin_model.final_status = 'Green'
    #         admin_model.save()
    #         return True
    #     except Exception as ex:
    #         #printstr(ex))
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return False

    # Insert update Admin Order Details view
    # def insert_update_admin_order_detail(self,payload):
    #     try:
    #         session_id = payload['session_id']
    #         order_id = payload['order_id']
    #         txn_id = payload['txn_id']
    #         # model objects
    #         cust_model = Model.customer_info.objects.get(session_id = session_id)
    #         order_obj = Model.order.objects.filter(order_id = order_id).last()
    #         customer_type = cust_model.customer_type
    #         service_type_id = cust_model.service_type_id
    #         service_model = Model.service_detail.objects.filter(customer_type = customer_type,service_type_id = service_type_id).last()
    #         promocode_model = Model.PromoCodes.objects.filter(customer_info = session_id).last()
    #         dl_model = Model.dl_manual_response.objects.filter(order = order_id).last()
    #         crime_model = Model.dl_manual_response.objects.filter(order = order_id).last()
            
    #         # save details in Admin Model
    #         admin_model = Model.AdminOrderModel()
    #         admin_model.customer_info = cust_model
    #         admin_model.order_id = order_id

    #         if cust_model.customer_type == '1':                
    #             # if cust_model.service_type_id in self.kyc_list:    
    #             #     admin_model.customer_name = 'NA'
    #             # else:
    #             admin_model.customer_name = (cust_model.name).upper()
    #             admin_model.mobile_number = cust_model.mobile_no
    #         elif cust_model.customer_type == '2' or cust_model.customer_type == '3':
    #             lookup_model = Model.customer_lookup.objects.filter(customer_info = session_id).last()                
    #             # if cust_model.service_type_id in self.kyc_list:    
    #             #     admin_model.customer_name = 'NA'
    #             # else:
    #             admin_model.customer_name = (lookup_model.vendor_name).upper()
    #             admin_model.mobile_number = lookup_model.vendor_mobile

    #         # save package detail
    #         package_name = service_model.service_type_name

    #         # get final amount
    #         if txn_id == "Coupon Code":
    #             admin_model.package_name = package_name
    #             admin_model.package_price = "--"
                
    #             admin_model.transaction_id = txn_id
    #             admin_model.payment_recieved_date = "--"#(datetime.now()).strftime("%d-%m-%Y, %H:%M:%S")
    #         else:
    #             package_price = service_model.service_type_price
    #             # amount = service_model.service_type_price
    #             # total_amount = amount
    #             # discount = service_model.service_type_discount
    #             final_amount = cust_model.final_price

    #             admin_model.package_name = package_name
    #             admin_model.package_price = str(package_price)
                
    #             admin_model.transaction_id = txn_id
    #             admin_model.payment_recieved_date = datetime.now()

    #         if cust_model.payment_status == True:
    #             admin_model.report_sent_time = None
    #         else:
    #             admin_model.report_sent_time = 'NA'

    #         admin_model.auto_or_manual = '--' #for auto/manual
    #         admin_model.final_status = "--" #for final status

    #         if txn_id == "Coupon Code":
    #             admin_model.final_amount = "--"
    #             admin_model.discount = "--"
    #         else:
    #             admin_model.final_amount = str(final_amount)
    #             if promocode_model:
    #                 admin_model.discount = str(promocode_model.discount_percentage) + '%'
    #             else:
    #                 admin_model.discount = 'NA'

    #         admin_model.save()

    #         return True
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return False

    # Insert update Admin Incomplete Transaction Details view
    # def insert_update_admin_incomplete_trans(self,payload):
    #     try:
    #         session_id = payload['session_id']

    #         # model objects
    #         cust_model = Model.customer_info.objects.get(session_id = session_id)

    #         # hellov
    #         if 'start' in payload:
    #             # save into admin model
    #             admin_model = Model.AdminIncompleteTransactionModel()
                
    #             admin_model.customer_info = payload['cust_obj']
    #             admin_model.id_uploaded = '--'
    #             admin_model.customer_type = '--'
    #             admin_model.package_name = '--'
    #             admin_model.mobile_number = payload['cust_obj'].mobile_no
    #             # admin_model.last_message_time = (datetime.now()).strftime("%d-%m-%Y, %H:%M:%S")
    #             admin_model.save()

    #             # making entry in customer_origin table
    #             # origin_obj = Model.customer_origin()
    #             # origin_obj.session_id = session_id
    #             # origin_obj.starts_with = payload['start'].upper()
    #             # origin_obj.mobile_no = cust_model.mobile_no
    #             # origin_obj.save()

    #         if "msg_at" in payload:
    #             admin_model = Model.AdminIncompleteTransactionModel()
    #             admin_model.last_message_time = (datetime.now()).strftime("%d-%m-%Y, %H:%M:%S")
    #             admin_model.save()

    #         if "customer_type" in payload:
    #             admin_model = Model.AdminIncompleteTransactionModel.objects.filter(customer_info=session_id).last()
    #             if cust_model.customer_type == '1':
    #                 admin_model.customer_type = "Myself"
    #             elif cust_model.customer_type == '2':
    #                 admin_model.customer_type = "Someone Else"
    #             # admin_model.last_message_time = (datetime.now()).strftime("%d-%m-%Y, %H:%M:%S")
    #             admin_model.save()

    #         if "service_type_id" in payload:
    #             customer_type = cust_model.customer_type
    #             service_type_id = cust_model.service_type_id
    #             service_model = Model.service_detail.objects.filter(customer_type = customer_type,service_type_id = service_type_id).last()
    #             package_name = service_model.service_type_name
                
    #             # update package in admin model
    #             admin_model = Model.AdminIncompleteTransactionModel.objects.filter(customer_info=session_id).last()
    #             admin_model.package_name = package_name
    #             # admin_model.last_message_time = (datetime.now()).strftime("%d-%m-%Y, %H:%M:%S")
    #             admin_model.save()

    #         if "id_upload" in payload:
    #             # update customer name in admin model
    #             admin_model = Model.AdminIncompleteTransactionModel.objects.filter(customer_info=session_id).last()
    #             if cust_model.adhaar_number:
    #                 admin_model.id_uploaded = cust_model.adhaar_number
    #             elif cust_model.dl_number:
    #                 admin_model.id_uploaded = cust_model.dl_number
    #             # admin_model.last_message_time = (datetime.now()).strftime("%d-%m-%Y, %H:%M:%S")
    #             admin_model.save()

    #         if "link_status" in payload:
    #             # update customer name in admin model
    #             admin_model = Model.AdminIncompleteTransactionModel.objects.filter(customer_info=session_id).last()
    #             if cust_model.adhaar_number:
    #                 admin_model.id_uploaded = 'Aadhaar'
    #             elif cust_model.dl_number:
    #                 admin_model.id_uploaded = 'Driving Licence'
    #             admin_model.payment_link_status = "Sent"
    #             # admin_model.last_message_time = (datetime.now()).strftime("%d-%m-%Y, %H:%M:%S")
    #             admin_model.save()

    #         return True
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return False  

    # Insert update Admin Incomplete Transaction Details view
    # def insert_admin_consent(self,payload):
    #     try:
    #         admin_model = Model.AdminConsentModel()
    #         admin_model.order_id = payload['order_id']
    #         # admin_model.cust_obj = payload['cust_obj']
    #         admin_model.customer_name = payload['name']
    #         admin_model.mobile_number = payload['mobile']
    #         admin_model.customer_type = "Customer"
    #         # admin_model.consent_time = (datetime.now()).strftime("%d-%m-%Y, %H:%M:%S")
    #         admin_model.save()

    #         return True
    #     except Exception as ex:
            
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return False  

    # delete entry for the AdminIncompleteTransactionModel after successful payment
    def delete_entry(self, payload):
        session_id = payload['session_id']
        Model.AdminIncompleteTransactionModel.objects.filter(session_id = session_id).delete()
        Model.reminder.objects.filter(customer_info = session_id).delete()
        return True
    
    # get kyc data for report i.e. selfie, sign etc.
    # def delete_entry(self, payload):
    #     session_id = payload['session_id']
    #     Model.AdminIncompleteTransactionModel.objects.filter(session_id = session_id).delete()
    #     Model.reminder.objects.filter(session_id = session_id).delete()
    #     return True
    
    # send first message to candidate to start the varification process
    def send_message_to_candidate(self, payload):
        try:
            session_id = payload['session_id'] 
            cust_lookup = Model.customer_lookup.objects.get(customer_info = session_id)
            order_obj = Model.order.objects.get(customer_info = session_id)
            candidate_mobile = cust_lookup.candidate_mobile

            obj_ques = Model.question_master.objects.get(question_id = 300)
            question_desc_eng = obj_ques.question_desc_eng
            question_desc_hindi = obj_ques.question_desc_hindi
            
            #add dynamic values
            question_desc_eng = question_desc_eng.replace('{{2}}', (cust_lookup.vendor_name).upper())
            question_desc_eng = question_desc_eng.replace('{{3}}', order_obj.order_id)
            question_desc_eng = question_desc_eng.replace('{{1}}', (cust_lookup.candidate_name).upper())
            question_desc_hindi = question_desc_hindi.replace('{{3}}', (cust_lookup.vendor_name).upper())
            question_desc_hindi = question_desc_hindi.replace('{{2}}', order_obj.order_id)
            question_desc_hindi = question_desc_hindi.replace('{{1}}', (cust_lookup.candidate_name).upper())
            pay_obj = processor.DB_Processor()
            pay_obj.sent_reminder(candidate_mobile, question_desc_eng)
            pay_obj.sent_reminder(candidate_mobile, question_desc_hindi)
            return True
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def detect_face(self, img_url, sid):
        try:
            import requests # to get image from the web
            import shutil # to save it locally
            img_name = str(sid) + '.jpg'
            r = requests.get(img_url, stream = True)

            # Check if the image was retrieved successfully
            if r.status_code == 200:
                # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                r.raw.decode_content = True                
                # Open a local file with wb ( write binary ) permission.
                with open(img_name,'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                    
            img_obj = cv2.imread(img_name,0)
            face_img = img_obj.copy()
            
            face_cascade = cv2.CascadeClassifier('hv_whatsapp_api//hv_whatsapp_backend//haarcascades//haarcascade_frontalface_default.xml')    
            face_rects = face_cascade.detectMultiScale(face_img,scaleFactor=1.2, minNeighbors=3, minSize=(100,100)) 
            
            eye_cascade = cv2.CascadeClassifier('hv_whatsapp_api//hv_whatsapp_backend//haarcascades//haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(face_img,scaleFactor=1.2, minNeighbors=5)
            
            os.remove(img_name)

            return (int(len(face_rects)) == 1 or int(len(eyes)) == 2)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False


#-------------------------QC GIFT CARD RELATED FUNCTIONS---------------

    def getQcToken(self,cust_obj):
        time_threshold = datetime.now() - timedelta(minutes=10080)
        qc_token = Model.qc_auth_tokens.objects.filter(updated_at__gt=time_threshold).last()
        print(str(qc_token))
        if qc_token:
            return qc_token.auth_token
        if app_settings.QC_TEST:
            url = app_settings.EXTERNAL_API['QC_TEST']+"authorize"
        else:
            url = app_settings.EXTERNAL_API['QC_PROD']+"authorize"
        if app_settings.QC_TEST:
            dataload = json.dumps({
                "UserName": "hv.int",
                "Password": "hvint@123",
                "ForwardingIntityId": "com.hv",
                "ForwardingIntityPassword": "comhv123",
                "TerminalId": "HV_Terminal"
            })
        else:
            dataload = json.dumps({
                "UserName": "helloverify.intuser",
                "Password": "h3ll0v3r1fy@1ntu53r",
                "ForwardingIntityId": "com.helloverify",
                "ForwardingIntityPassword": "C0m@h3ll0v3r1fy",
                "TerminalId": "Hello Verify-Corporate-01"
            
            })

        headers = {
            'DateAtClient': datetime.today().strftime('%Y-%m-%d')+ "T"+ datetime.now().strftime("%H:%M:%S"),
            'Content-Type': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=dataload)
        print(json.loads(response.text).get('AuthToken'))
        Model.qc_api_log(customer_info=cust_obj,url=url,request_payload=str(dataload),response=str(json.loads(response.text)),headers=str(headers)).save()
        Model.qc_auth_tokens(auth_token=json.loads(response.text).get('AuthToken')).save()
        return json.loads(response.text).get('AuthToken')

    def validate_gift_card(self, payload):
        try:
            if (not payload['input_data'].split(',')[0].isdigit() or not(len(payload['input_data'].split(',')[0]) == 16) or not payload['input_data'].split(',')[1].isdigit() or not(len(payload['input_data'].split(',')[1]) == 6)):
                payload['results'] = 'gift_card_invalid'
                return payload           

            cust_obj = Model.customer_info.objects.filter(session_id=payload['session_id']).last()
            
            auth_token = self.getQcToken(cust_obj)

            if app_settings.QC_TEST:
                url3 = app_settings.EXTERNAL_API['QC_TEST']+"gc/transactions/validate"
            else:
                url3 = app_settings.EXTERNAL_API['QC_PROD']+"gc/transactions/validate"

            dataload3 = json.dumps({
            "TransactionTypeId": "306",
            "InputType": "1",
            "Cards": [
                {
                "CardNumber": payload['input_data'].split(',')[0],
                "CardPIN": payload['input_data'].split(',')[1]
                }
            ]
            })
            headers3 = {
            'DateAtClient': datetime.today().strftime('%Y-%m-%d')+ "T"+ datetime.now().strftime("%H:%M:%S"),
            'Authorization': 'Bearer '+auth_token,
            'Content-Type': 'application/json'
            }

            response3 = requests.request("POST", url3, headers=headers3, data=dataload3)
            Model.qc_api_log(customer_info=cust_obj,url=url3,request_payload=str(dataload3),response=str(json.loads(response3.text)),headers=str(headers3)).save()

            if json.loads(response3.text).get('Cards')[0].get('CardStatus') == 'Activated':
                if json.loads(response3.text).get('Cards')[0].get('Balance') == 849:
                    payload['results'] = 'gift_card_valid_799'
                    cust_obj.gift_card = payload['input_data'].split(',')[0]
                    cust_obj.gift_card_pin =payload['input_data'].split(',')[1]
                    cust_obj.gift_card_balance = 849
                    cust_obj.save()

                elif json.loads(response3.text).get('Cards')[0].get('Balance') == 1499:
                    payload['results'] = 'gift_card_valid_1499'
                    cust_obj.gift_card = payload['input_data'].split(',')[0]
                    cust_obj.gift_card_pin =payload['input_data'].split(',')[1]
                    cust_obj.gift_card_balance = 1499
                    cust_obj.save()
                else:
                    payload['results'] = 'gift_card_insuf_balance'

            elif not json.loads(response3.text).get('Cards')[0].get('CardStatus',None):
                payload['results'] = 'gift_card_invalid'
            else:
                payload['results'] = 'gift_card_expired'
            return payload    

        except:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload           

    def sent_reminder(self,mobile, mesg, url=None):
        from twilio.rest import Client
        account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
        auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
        client = Client(account_sid, auth_token)
        if app_settings.LOCAL_ENV == False:
            message = client.messages \
                .create(
                    media_url=[url],
                    from_='whatsapp:+14157924931',
                    body=mesg,
                    to='whatsapp:'+mobile
                )

    def redeem_call(self,url, headers, dataload,cust_obj):
        language_type = cust_obj.language_type      
        for i in range(2):
            headers['DateAtClient'] = datetime.today().strftime('%Y-%m-%d')+ "T"+ datetime.now().strftime("%H:%M:%S")
            qc_log = Model.qc_api_log.objects.create(customer_info=cust_obj,url=url,\
                    request_payload=dataload,headers=headers)
            try:
                resp = requests.request("POST", url, headers=headers, data=dataload,timeout=21)
                qc_log.response = str(json.loads(resp.text))
                qc_log.save()
                return json.loads(resp.text)
            except Exception as ex:
                qc_log.response = str(ex)
                qc_log.save()
                if i == 0:
                    # if language_type == 1:
                    #     self.sent_reminder(cust_obj.mobile_no, 'We are processing your request. \n*Please wait.*\n')
                    #     # pay_obj.create_thread(cust_obj.mobile_no, 'We are processing your request. \n*Please wait.*\n')
                    # elif language_type == 2:
                    #     self.sent_reminder(cust_obj.mobile_no, 'हम आपके निवेदन पर कार्य कर रहे हैं। \n*कृपया प्रतीक्षा करें।*\n')
                    time.sleep(18)
        else:
            if language_type == 1:
                self.sent_reminder(cust_obj.mobile_no, 'Due to some internal error currently we are not able to process your request. \n\nPlease email us at hellov@helloverify.com')
            elif language_type == 2:
                self.sent_reminder(cust_obj.mobile_no, 'कुछ आंतरिक गलती के कारण अभी हम आपके अनुरोध को पूरा नहीं कर सकते। \n\nकृपया हमें hellov@helloverify.com पर ईमेल करें।')
            resp = {"error":True}
            return  resp

    def redeem_gift_card(self, payload):
        try:
            cust_obj = Model.customer_info.objects.filter(session_id=payload['session_id']).last()

            auth_token = self.getQcToken(cust_obj)

            if app_settings.QC_TEST:
                url = app_settings.EXTERNAL_API['QC_TEST']+"gc/transactions"
            else:
                url = app_settings.EXTERNAL_API['QC_PROD']+"gc/transactions"

            dataload = json.dumps({
            "TransactionTypeId": "302",
            "IdempotencyKey": "HV"+str(cust_obj.session_id),
            "InvoiceNumber": "HV"+str(cust_obj.session_id),
            "InvoiceAmount": cust_obj.gift_card_balance,
            "Notes": "Service: "+str(cust_obj.service_type_id),
            "InputType": "1",
            "NumberOfCards": "1",
            "Cards": [
                {
                "CardNumber": cust_obj.gift_card,
                "CardPin": cust_obj.gift_card_pin,
                "Amount": cust_obj.gift_card_balance
                }
            ]
            })
            headers = {
            'TransactionId': str(cust_obj.session_id),
            'Authorization': 'Bearer '+auth_token,
            'Content-Type': 'application/json'
            }

            response = self.redeem_call(url, headers, dataload,cust_obj)
            
            if response.get('error', None) == True:
                quit()

            Model.qc_api_log.objects.create(customer_info=cust_obj,url=url,\
                request_payload=str(dataload),response=str(response),\
                    headers=str(headers))
            
            if response.get('Cards')[0].get('TransactionAmount') == cust_obj.gift_card_balance:
                cust_obj.final_price = cust_obj.gift_card_balance
                cust_obj.payment_status = True
                cust_obj.save()

                if cust_obj.service_type_id > 26: #for myself
                    customer_type_payload = {}
                    customer_type_payload["user_action"] = '1'
                    status = "skip_customer_type"
                else: #for someone else
                    customer_type_payload = {}
                    customer_type_payload["user_action"] = '2'
                    status = "skip_customer_type_someone"
                    payload['new_customer_type'] = '2'
                customer_type_payload["session_id"] = payload['cust_obj'].session_id
                customer_type_payload["mobile_no"] = cust_obj.mobile_no
                self.save_customer_type(customer_type_payload)
                payload['user_action'] = None
                payload['results'] = status

            else:
                payload['results'] = 'gift_card_invalid'
            return payload

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = 'incorrect_input'
            return payload
            
#-------------------------QC GIFT CARD RELATED FUNCTIONS---------------



    # send first message to candidate to start the varification process
    def save_badge_selfie(self, payload):
        try:
            status = self.detect_face(payload['url'], payload['session_id'])
            if status:
                cust_obj = Model.customer_info.objects.get(session_id = payload['session_id'])
                cust_obj.selfie_url = payload['url']
                cust_obj.save()
                payload['results'] = 'correct_input'
                return payload
            else:
                payload['results'] = 'invalid_selfie'
                return payload
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def kyc_check(self, payload):
        try:
            kyc_obj = Model.kyc_report_data.objects.get(customer_info = payload['session_id'])
            if not kyc_obj.selfie_url:
                kyc_obj.selfie_url = payload['url']
            elif not kyc_obj.gate_url:
                kyc_obj.gate_url = payload['url']
            elif not kyc_obj.vehicle_or_sign_url:
                kyc_obj.vehicle_or_sign_url = payload['url']
            elif not kyc_obj.front_img_url:
                kyc_obj.front_img_url = payload['url']
            elif not kyc_obj.back_img_url:
                kyc_obj.back_img_url = payload['url']
            kyc_obj.save()
            payload['results'] = 'correct_input'
            return payload
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def get_map_location(self, payload):
        try:
            kyc_obj = Model.kyc_report_data()
            kyc_obj.customer_info = payload['cust_obj']
            kyc_obj.actual_lat_long = payload['Latitude'] + ',' + payload['Longitude']
            kyc_obj.save()
            payload['results'] = 'correct_input'
            return payload
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    def match_uan_otp(self, payload):
        try:
            
            payload['results'] = 'correct_input'
            return payload
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    # calcualte coupon redeem time 
    def coupon_redeem_time(self,coupon_code, mobile_no):
        try:
            # check redem time
            check_coupon_model = Model.UniqueCodes.objects.filter(code = coupon_code).last()

            if check_coupon_model.redeem_time == None or check_coupon_model.mobile_no == mobile_no:
                return True
            else:
                redeem_time = check_coupon_model.redeem_time.split(".")
                redeem_time = redeem_time[0]

                redeem_time = datetime.strptime(redeem_time, '%Y-%m-%d %H:%M:%S')
                current_time = datetime.now()

                time_diff = (current_time - redeem_time)
                total_seconds = time_diff.total_seconds()
                minutes = total_seconds/60

                if minutes >= 60:                    
                    return True 
                
            return False

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    validate coupon code for incorrect, correct, block and prevent brute force attack
    '''
    def validate_coupon(self, payload): #call save service type and save service type = 21, 22 etc
        status = "exception"
        try:
            mobile_no = payload['mobile_no']
            coupon_code = payload['input_data'].upper().replace(' ', '').replace('*', '')
            # cust_obj = Model.customer_info.objects.get(session_id = payload['session_id'])
            # check correct coupon_code
    
            check_coupon_model = Model.UniqueCodes.objects.filter(code=coupon_code, is_redeemed=False, is_distributed=True).last()
            if check_coupon_model: # coupon exist
                res = self.coupon_redeem_time(coupon_code, mobile_no)
                validate_redeempin_for_strors(coupon_code,mobile_no)
                validate_redeempin_for_partners(coupon_code,mobile_no)
                #mail sending logic
                subject = "Trying to redeem coupon"
                content = "Please check someone tried to reddem coupon - "+coupon_code
                mail_process = mail.Send_Email()
                mail_process.process(subject,content)
                #mail sending logic end
                
                if res:
                    pass
                else:
                    cust_coupon_code_model = Model.customer_coupon_code.objects.filter(mobile_no = mobile_no).last()
                    if cust_coupon_code_model and cust_coupon_code_model.allowed_attempt <= 1:
                        cust_coupon_code_model.allowed_attempt = cust_coupon_code_model.allowed_attempt - 1
                        cust_coupon_code_model.allowed = False
                        cust_coupon_code_model.save()
                        status = "blocked_user"
                    elif cust_coupon_code_model:
                        status = "invalid_coupon"
                        cust_coupon_code_model.allowed_attempt = cust_coupon_code_model.allowed_attempt - 1
                        cust_coupon_code_model.last_attempt_time = datetime.now()
                        cust_coupon_code_model.save()
                    payload['results'] = status
                    return payload
                # check status in customer coupon code model
                cust_coupon_code_model = Model.customer_coupon_code.objects.filter(mobile_no = mobile_no).last()
                if cust_coupon_code_model: # if entry exist in customer coupon code model
                    allowed = cust_coupon_code_model.allowed
                    if not allowed:
                        last_attempt = cust_coupon_code_model.last_attempt_time
                        current_attempt = datetime.now()
                        time_diff = (current_attempt - last_attempt)
                        total_seconds = time_diff.total_seconds()
                        minutes = total_seconds/60
                        hours = int(minutes/60)
                        if hours >= 24: 
                            allowed = True
                            cust_coupon_code_model.allowed = allowed
                            cust_coupon_code_model.allowed_attempt = 3
                            cust_coupon_code_model.save()
                            status = "valid_coupon"
                        else:
                            status = "blocked_user"
                    else:
                        status = "valid_coupon"
                else: # if entry does not exist in customer coupon code model
                    cust_coupon_code_model = Model.customer_coupon_code()
                    cust_coupon_code_model.mobile_no = mobile_no
                    cust_coupon_code_model.last_attempt_time = datetime.now()
                    cust_coupon_code_model.allowed = True
                    cust_coupon_code_model.save()
                    status = "valid_coupon"
                # return status, hours
            else: # coupon does not exist
                # check status in customer coupon code model
                cust_coupon_code_model = Model.customer_coupon_code.objects.filter(mobile_no = mobile_no).last()
                if cust_coupon_code_model: # if entry exist in customer coupon code model
                    allowed = cust_coupon_code_model.allowed
                    last_attempt = (cust_coupon_code_model.last_attempt_time).replace(tzinfo=None)
                    current_attempt = datetime.now().replace(tzinfo=None)
                    time_diff = (current_attempt - last_attempt)
                    total_seconds = time_diff.total_seconds()
                    minutes = total_seconds/60
                    hours = int(minutes/60)
                    if hours >= 24: # if time difference in hours is more than 24 hours
                        allowed = True
                        cust_coupon_code_model.last_attempt_time = datetime.now()
                        cust_coupon_code_model.allowed_attempt = 2
                        cust_coupon_code_model.allowed = True
                        cust_coupon_code_model.save()
                    else: # if time difference in hours is less than 24 hours
                        if cust_coupon_code_model.allowed_attempt > 0:
                            cust_coupon_code_model.allowed_attempt = cust_coupon_code_model.allowed_attempt - 1
                            cust_coupon_code_model.last_attempt_time = datetime.now()
                            cust_coupon_code_model.save()
                        else:
                            allowed = False
                            # cust_coupon_code_model.last_attempt_time = datetime.now()
                            cust_coupon_code_model.allowed = allowed
                            cust_coupon_code_model.save()
                    if cust_coupon_code_model.allowed_attempt == 0:
                        allowed = False
                        cust_coupon_code_model.allowed = allowed
                        cust_coupon_code_model.save()
                    if not allowed:
                        status = "blocked_user"
                    else:
                        status = "invalid_coupon"
                else: # if entry does not exist in customer coupon code model
                    cust_coupon_code_model = Model.customer_coupon_code()
                    cust_coupon_code_model.mobile_no = mobile_no
                    cust_coupon_code_model.allowed_attempt = 2
                    cust_coupon_code_model.last_attempt_time = datetime.now()
                    cust_coupon_code_model.allowed = True
                    cust_coupon_code_model.save()
                    status = "invalid_coupon"
                # return status, hours
            if status == "valid_coupon":
                #save service_type_id based on coupon code
                # payload['session_id'] = payload['session_id']
                payload["user_action"] = check_coupon_model.service_type_id
                self.save_service_type(payload)
                payload["user_action"] = None
                # check_coupon_model.is_redeemed = True
                check_coupon_model.mobile_no = mobile_no
                check_coupon_model.customer_info = payload['cust_obj']
                check_coupon_model.redeem_time = datetime.now()
                check_coupon_model.save()

                if check_coupon_model.service_type_id > 26 and check_coupon_model.service_type_id !=29: #for myself (Here second condition is for know your contact check)
                    customer_type_payload = {}
                    customer_type_payload["user_action"] = '1'
                    status = "skip_customer_type"
                else: #for someone else
                    customer_type_payload = {}
                    customer_type_payload["user_action"] = '2'
                    status = "skip_customer_type_someone"
                    payload['new_customer_type'] = '2'
                customer_type_payload["session_id"] = payload['cust_obj'].session_id
                customer_type_payload["mobile_no"] = mobile_no
                self.save_customer_type(customer_type_payload)
                payload['user_action'] = None
            payload['results'] = status
            return payload
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            payload['results'] = status
            return payload

    def is_user_allowed(self, mobile_no):
        cust_promocode_obj = Model.customer_promocode.objects.filter(mobile_no = mobile_no).last()
        if cust_promocode_obj: # if entry exist in customer promocode model
            allowed = cust_promocode_obj.allowed
            if not allowed:
                last_attempt = cust_promocode_obj.last_attempt_time
                current_attempt = datetime.now()
                time_diff = (current_attempt - last_attempt)
                total_seconds = time_diff.total_seconds()
                minutes = total_seconds/60
                hours = int(minutes/60)
                if hours >= 24: 
                    allowed = True
                    cust_promocode_obj.allowed = allowed
                    cust_promocode_obj.allowed_attempt = 3
                    cust_promocode_obj.save()
                    status = "valid_coupon"
                else:
                    status = "blocked_user"
            else:
                status = "valid_coupon"
        else: # if entry does not exist in customer promocode code model
            cust_promocode_obj = Model.customer_promocode()
            cust_promocode_obj.mobile_no = mobile_no
            cust_promocode_obj.last_attempt_time = datetime.now()
            cust_promocode_obj.allowed = True
            cust_promocode_obj.save()
            status = "valid_coupon"
        return status


    # calcualte coupon redeem time 
    def promocode_redeem_time(self,promocode, mobile_no):
        try:
            # check redem time
            promocode_obj = Model.PromoCodes.objects.filter(code = promocode).last()

            if promocode_obj.redeem_time == None or promocode_obj.mobile_no == mobile_no:
                return True
            else:
                redeem_time = promocode_obj.redeem_time
                
                current_time = datetime.now()

                time_diff = (current_time - redeem_time)
                total_seconds = time_diff.total_seconds()
                minutes = total_seconds/60

                if minutes >= 60:                    
                    return True 
                
            return False

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False


    # '''
    # validate promocode for incorrect, correct, block and prevent brute force attack
    # '''
    # def validate_promocode(self, payload): #call save service type and save service type = 21, 22 etc
    #     status = "exception"
    #     try:
    #         cust_obj = Model.customer_info.objects.get(session_id = payload['session_id'])
    #         service_obj = Model.service_detail.objects.filter(service_type_id = cust_obj.service_type_id, customer_type = cust_obj.customer_type).last()
    #         if cust_obj and payload['user_action'] == 2:
    #             cust_obj.final_price = service_obj.service_type_price
    #             cust_obj.save()
    #             payload['results'] = 'correct_input'
    #             return payload            
    #         mobile_no = payload['mobile_no']
    #         promocode = payload['input_data'].upper()
            
    #         gpromocode_obj = Model.GeneralPromoCodes.objects.filter(code = promocode, is_expired = False).last()
            
    #         if gpromocode_obj:
    #             status = self.is_user_allowed(mobile_no)
    #             if status == "blocked_user":
    #                 payload['results'] = 'blocked_user'
    #                 return payload    
    #             cust_obj.final_price = int(service_obj.service_type_price * (1 - gpromocode_obj.discount_percentage/100))
    #             cust_obj.promo_applied = gpromocode_obj.code
    #             cust_obj.save()                
    #             payload['results'] = 'valid_coupon'
    #             return payload

    #         promocode_obj = Model.PromoCodes.objects.filter(code = promocode, is_redeemed = False).last()
            
    #         if promocode_obj: # promocode exist
    #             res = self.promocode_redeem_time(promocode, mobile_no)
    #             if res:
    #                 pass
    #             else:
    #                 cust_promocode_obj = Model.customer_promocode.objects.filter(mobile_no = mobile_no).last()
    #                 if cust_promocode_obj and cust_promocode_obj.allowed_attempt <= 1:
    #                     cust_promocode_obj.allowed_attempt = cust_promocode_obj.allowed_attempt - 1
    #                     cust_promocode_obj.allowed = False
    #                     cust_promocode_obj.save()
    #                     status = "blocked_user"
    #                 elif cust_promocode_obj:
    #                     status = "invalid_coupon"
    #                     cust_promocode_obj.allowed_attempt = cust_promocode_obj.allowed_attempt - 1
    #                     cust_promocode_obj.last_attempt_time = datetime.now()
    #                     cust_promocode_obj.save()
    #                 payload['results'] = status
    #                 return payload
    #             # check status in customer promocode code model
    #             status = self.is_user_allowed(mobile_no)

    #         else: # promocode does not exist
    #             # check status in customer promocode model
    #             cust_promocode_obj = Model.customer_promocode.objects.filter(mobile_no = mobile_no).last()
    #             if cust_promocode_obj: # if entry exist in customer promocode model
    #                 allowed = cust_promocode_obj.allowed
    #                 last_attempt = (cust_promocode_obj.last_attempt_time).replace(tzinfo=None)
    #                 current_attempt = datetime.now().replace(tzinfo=None)
    #                 time_diff = (current_attempt - last_attempt)
    #                 total_seconds = time_diff.total_seconds()
    #                 minutes = total_seconds/60
    #                 hours = int(minutes/60)
    #                 if hours >= 24: # if time difference in hours is more than 24 hours
    #                     allowed = True
    #                     cust_promocode_obj.last_attempt_time = datetime.now()
    #                     cust_promocode_obj.allowed_attempt = 2
    #                     cust_promocode_obj.allowed = True
    #                     cust_promocode_obj.save()
    #                 else: # if time difference in hours is less than 24 hours
    #                     if cust_promocode_obj.allowed_attempt > 0:
    #                         cust_promocode_obj.allowed_attempt = cust_promocode_obj.allowed_attempt - 1
    #                         cust_promocode_obj.last_attempt_time = datetime.now()
    #                         cust_promocode_obj.save()
    #                     else:
    #                         allowed = False
    #                         # cust_promocode_obj.last_attempt_time = datetime.now()
    #                         cust_promocode_obj.allowed = allowed
    #                         cust_promocode_obj.save()
    #                 if cust_promocode_obj.allowed_attempt == 0:
    #                     allowed = False
    #                     cust_promocode_obj.allowed = allowed
    #                     cust_promocode_obj.save()
    #                 if not allowed:
    #                     status = "blocked_user"
    #                 else:
    #                     status = "invalid_coupon"
    #             else: # if entry does not exist in customer promocode model
    #                 cust_promocode_obj = Model.customer_promocode()
    #                 cust_promocode_obj.mobile_no = mobile_no
    #                 cust_promocode_obj.allowed_attempt = 2
    #                 cust_promocode_obj.last_attempt_time = datetime.now()
    #                 cust_promocode_obj.allowed = True
    #                 cust_promocode_obj.save()
    #                 status = "invalid_coupon"
    #             # return status, hours
    #         if status == "valid_coupon":
    #             #save service_type_id based on promocode
    #             # payload['session_id'] = payload['session_id']
    #             # payload["user_action"] = promocode_obj.service_type_id
    #             # self.save_service_type(payload)
    #             # payload["user_action"] = None
    #             # promocode_obj.is_redeemed = True
    #             promocode_obj.mobile_no = mobile_no
    #             promocode_obj.customer_info = cust_obj
    #             promocode_obj.redeem_time = datetime.now()
    #             promocode_obj.save()
    #             cust_obj.final_price = int(service_obj.service_type_price * (1 - promocode_obj.discount_percentage/100))
    #             cust_obj.save()
    #         payload['results'] = status
    #         return payload
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         payload['results'] = status
    #         return payload

    #generate coupon codes for service type 21, 22, 23, 24, 25, 26
    def generate_coupon_codes(self):
        code_obj = Model.UniqueCodes.objects.all().exclude(code_type = 'online')
        for item in code_obj:
            item.code_type = 'offline'
            item.save()
        # code_obj = Model.UniqueCodes.objects.all().exclude(code_type = 'online')
        # for item in code_obj:
        #     item.code_type = 'online'
        #     item.save()
        # code_obj = Model.UniqueCodes.objects.all().exclude(code_type = 'online')
        # for item in code_obj:
        #     item.code_type = 'online'
        #     item.save()
        # code_obj = Model.UniqueCodes.objects.filter(id__gte=32807, id__lt=32807+2000)
        # for item in code_obj:
        #     item.code_type = 'online'
        #     item.save()
        # code_obj = Model.UniqueCodes.objects.filter(id__gte=41007, id__lt=41007+2000)
        # for item in code_obj:
        #     item.code_type = 'online'
        #     item.save()
        # for i in range(2000):
        #     code_obj = Model.UniqueCodes()
        #     code_obj.service_type_id = 23
        #     code_obj.save()
        # for i in range(2000):
        #     code_obj = Model.UniqueCodes()
        #     code_obj.service_type_id = 24
        #     code_obj.save()
        # for i in range(2000):
        #     code_obj = Model.UniqueCodes()
        #     code_obj.service_type_id = 25
        #     code_obj.save()
        # for i in range(2000):
        #     code_obj = Model.UniqueCodes()
        #     code_obj.service_type_id = 26
        #     code_obj.save()
        #print'done')
    

    # Organize all function in a dictionary call
    def call_func(self, key, payload):

        call_by_name = {
            'save_language_type': self.save_language_type,
            'save_service_type': self.save_service_type,
            'save_id_type': self.save_id_type,
            'go_to_previous_ques': self.go_to_previous_ques,
            'parse_front_image': self.parse_front_image,
            'parse_back_image': self.parse_back_image,
            'save_UAN': self.save_uan,
            'payment_status_check': self.get_payment_status,
            'save_customer_type': self.save_customer_type,
            'save_candidate_mobile_no': self.save_candidate_mobile,
            'varification_done': '',
            'save_name': self.save_name,
            'validate_coupon': self.validate_coupon,
            'kyc_check': self.kyc_check,
            'get_map_location': self.get_map_location,            
            'save_badge_selfie': self.save_badge_selfie,
            'validate_gift_card': self.validate_gift_card,
            'redeem_gift_card': self.redeem_gift_card,
            
            # 'match_uan_otp': self.match_uan_otp,
        }
        try:
            execute = call_by_name[key](payload)
            return execute
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # def download_media_file(self, unique_id, url):
    #     try:
    #         import requests, time, os
    #         path = '/datadrive/media/edu/' + unique_id
                    
    #         if not os.path.exists(path):
    #             os.mkdir(path)

    #         r = requests.get(url, stream=True)
    #         ext = r.headers['content-type'].split('/')[-1] # converts response headers mime type to an extension (may not work with everything)

    #         file_name = path + '/' + str(time.time())
    #         with open("%s.%s" % (file_name, ext), 'wb') as f: # open the file to write as binary - replace 'wb' with 'w' for text files
    #             for chunk in r.iter_content(1024): # iterate on stream using 1KB packets
    #                 f.write(chunk) # write the file
    #         file_name = file_name.replace('/datadrive', '')
    #         return file_name + "." + ext
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return url

    def save_edu_doc(self, url, edu_obj):
        try:
            # url = self.download_media_file(edu_obj.unique_id, url)
            if not edu_obj.tenth_url:
                edu_obj.tenth_url = url
            elif not edu_obj.twelveth_url and (edu_obj.twelveth).lower() == 'yes':
                edu_obj.twelveth_url = url
            elif '-' == edu_obj.extra_urls:
                edu_obj.extra_urls = url
            else:
                edu_obj.extra_urls = str(edu_obj.extra_urls) + ',' + url
            # if 'Insuff_' in Model.edu_doc_status(edu_obj.case_status).name:
            #     edu_obj.case_status = '2'
            #     # Call oni api to clear insuff 
            #     edu_obj.insuff_oni_update = True
            edu_obj.save()
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ''

    def initiate_cowin_check(self, req_data, mobile_no):
        try:
            ques_obj = Model.question_master.objects.get(question_id = 2004)
            cowin_data = req_data.split('_')
            Model.CowinData.objects.create(
                check_id='COWIN_'+(secrets.token_hex(4)).upper(),
                whatsapp_mobile_no = mobile_no,
                name = cowin_data[1].strip(),
                birth_year = cowin_data[2].strip()
            )
            final_ques = ques_obj.question_desc_eng.format(name=cowin_data[1].strip().title(), \
                whatsapp_mobile_no=mobile_no[3:])
            return final_ques
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return 'Incorrect Input. Please give input in below format. \n\n*Cowin_FisrtName_BirthYear*'

    def call_cowin_apis(self, mobile_no, otp = None):
        try:
            if otp:
                url = app_settings.EXTERNAL_API['COWIN_URL']+"cowin/api/get_status/"
            else:
                url = app_settings.EXTERNAL_API['COWIN_URL']+"cowin/api/send_otp/"
            headers = {"Content-Type": "application/json"}
            data = {'mobile_no': mobile_no, 'otp':otp}
            api_result = requests.post(url, data=json.dumps(data), headers=headers)
            return api_result
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return "Incorrect Input. \n\n*Please give valid input.*"


    def get_cowin_details(self, req_data, cowin_obj):
        try:             
            if len(req_data) in (10, 1):
                if req_data == '1':
                    cowin_obj.cowin_mobile_no = cowin_obj.whatsapp_mobile_no
                else:
                    cowin_obj.cowin_mobile_no = '+91' + req_data
                cowin_obj.reminder_count -= 1
                api_result = self.call_cowin_apis(cowin_obj.cowin_mobile_no[3:])
                if api_result.status_code == 200:
                    if 'cowin_' in cowin_obj.check_id.lower():
                        ques = Model.question_master.objects.get(question_id = 2005)
                    else:
                        ques = Model.question_master.objects.get(question_id = 2002)
                    res = ques.question_desc_eng
                else:
                    res = 'Invalid mobile number'
            elif len(req_data) == 6:
                cowin_obj.cowin_otp = req_data
                api_result = self.call_cowin_apis(cowin_obj.cowin_mobile_no[3:],cowin_obj.cowin_otp)
                cowin_obj.api_result = api_result.text
                if api_result.status_code == 200:
                    load_res = json.loads(api_result.text)
                    if load_res.get('result', None):
                        if load_res['result'] == 'Incorrect OTP entered':
                            res = 'Invalid OTP Submitted'
                        else:
                            res = 'Something went wrong, please try after sometime'
                    else:
                        if 'cowin_' in cowin_obj.check_id.lower():
                            ques = Model.question_master.objects.get(question_id = 2006)
                            res = ques.question_desc_eng
                            report_url = views.generate_cowin_report(cowin_obj)
                            views.send_cowin_report(cowin_obj)
                        else:
                            ques = Model.question_master.objects.get(question_id = 2003)
                            res = ques.question_desc_eng.format(client_name = cowin_obj.client_name)
                            report_url = views.generate_cowin_report(cowin_obj)
                        cowin_obj.case_status = True
                        cowin_obj.report_url = report_url
                else:
                    res = 'Something went wrong, please try after sometime'
            cowin_obj.save()
            return res
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            cowin_obj.save()
            return 'Something went wrong, please try after sometime'

    def get_redemption_pin(self, service_type_id, mobile_no):
        code_obj = Model.UniqueCodes.objects.filter(service_type_id = service_type_id, is_redeemed=False, is_distributed=False).exclude(assigned_to="PayTM").first()
        try:
            code = code_obj.code
            # if '9205264013' not in mobile_no:
            code_obj.is_distributed = True
            code_obj.assigned_to = "NoBroker"
            code_obj.save()
            return code
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False