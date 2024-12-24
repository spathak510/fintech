import datetime
from django.db.models.base import Model
import time
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import (action,   parser_classes)
from rest_framework.permissions import AllowAny
import logging
log = logging.getLogger('MYAPP')
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
from urllib.request import urlopen, Request
import re, datetime
from hv_whatsapp_api.hv_whatsapp_backend import views as whatsapp_views
from hv_whatsapp_api import models
from hv_whatsapp_api import models as Model
from hv_whatsapp_api.hv_whatsapp_backend import whatsapp_backend_api, processor
import traceback
from hv_whatsapp_api.hv_whatsapp_backend import send_mail as mail
import logging
import inspect
import traceback
import threading
from django.core.cache import cache
from . import views as controller_view

logging.basicConfig(filename="error_log.log")
class Whatsapp_frontend(viewsets.ViewSet):
    queryset = models.Dummy.objects.all()
    appbackend = whatsapp_backend_api.Whatsapp_backend()
    service_mapping_799 = {1:25,2:26,3:28}
    service_mapping_1499 = {1:21,2:22,3:23,4:24,5:27}
    

    '''
    This api is hit by twilio to process the request from customer through WhatsApp.
    Hellov, Hello Redeem process initiation text is processed through this API.
    This function create, update for new customer and existing customers.
    Twilio message sednig function is called here to send the final message to the
    customer after processign the request of customer
    '''
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def whatsapp_controller_api(self, request):
        try:
            #print"START CHAT")
            start_time = time.time()
            response = MessagingResponse()
            data = request.data
            req_data = data['Body'].lower()
            mobile_str = data['From'] 
            mob_exp = '[+]?[0-9]{10,12}'
            mobile_no = re.search(mob_exp, mobile_str).group()   
            verify_now_obj = Model.VerifyNow.objects.filter(mobile_no=mobile_no, is_session_expired=False, is_active=True).last()
            # if 'claimed_address' in req_data.replace(' ', ''):
            #     claimed_address = req_data.split('---')[1]
            #     claimed_lat_long, location_json = controller_view.get_lat_long(claimed_address)
            #     Model.LatLong.objects.filter(mobile_no=mobile_no).delete()
            #     Model.LatLong.objects.create(mobile_no=mobile_no, claimed_lat_long=claimed_lat_long, location_json=location_json)
            #     msg = response.message('please share your current location')
            #     return HttpResponse(response)
            # elif 'Latitude' in data:
            #     lat_long_obj = Model.LatLong.objects.filter(mobile_no=mobile_no).last()
            #     if lat_long_obj:
            #         claimed_lat_long = lat_long_obj.claimed_lat_long
            #         actual_lat_long = data['Latitude'] + ',' + data['Longitude']
            #         map_url, is_match, distance = controller_view.find_location_match(claimed_lat_long, actual_lat_long)
            #         lat_long_obj.actual_lat_long = actual_lat_long
            #         lat_long_obj.map_url = map_url
            #         lat_long_obj.is_match = is_match
            #         lat_long_obj.distance = distance
            #         lat_long_obj.save()
            #         # if is_match:
            #         #     msg = response.message(map_url)
            #         # else:
            #         msg = response.message(map_url)
            #         return HttpResponse(response)
            if 'helloredeem' == req_data.replace(' ', ''):
                service_type_id = 20 
                cust_obj = Model.customer_info()
                cust_obj.mobile_no = mobile_no
                cust_obj.service_type_id = service_type_id
                cust_obj.save()
                session_id = cust_obj.session_id
                ms_payload = {'mobile_no':mobile_no, 'cust_obj': cust_obj, 'session_id':session_id, 'service_type_id': service_type_id}
                self.appbackend.save_mobile_session(ms_payload)   #save in session_map, customer_register, customer_info             
                nq_payload = {'cust_obj': cust_obj, 'session_id':session_id, 'prev_question_id': -1}
                res = self.appbackend.get_next_ques(nq_payload)
                next_ques = res['question_desc']
                next_question_id = res['next_question_id']
                s_payload = {'cust_obj': cust_obj, 'session_id':session_id, 'prev_question_id': 0, 'next_question_id': next_question_id, 'mobile_no': mobile_no, 'service_type_id': service_type_id} #all other parameters are null
                self.appbackend.save_session_log(s_payload)
                msg = response.message(next_ques)
                if verify_now_obj:
                    verify_now_obj.is_session_expired = True
                    verify_now_obj.save()
            elif 'hellov' == req_data.replace(' ', ''):
                verify_now_set = Model.VerifyNow.objects.filter(mobile_no=mobile_no, is_active=True)
                verify_now_set.update(is_active=False, is_session_expired=True)
                verify_now_obj = Model.VerifyNow()
                verify_now_obj.mobile_no = mobile_no
                question_desc_eng = cache.get('verifynow_3000')
                if question_desc_eng ==None:
                    Model.question_master.objects.get(question_id=3000).save()
                    question_desc_eng = cache.get('verifynow_3000')
                verify_now_obj.save()
                msg = response.message(question_desc_eng)
                Model.customer_info.objects.filter(mobile_no = mobile_no, payment_status=False).delete()       
            elif 'redeemnow' == req_data.replace(' ', ''):
                verify_now_set = Model.VerifyNow.objects.filter(mobile_no=mobile_no, is_active=True)
                verify_now_set.update(is_active=False, is_session_expired=True)                
                Model.customer_info.objects.filter(mobile_no=mobile_no, payment_status=False).delete()
                service_type_id = 20 
                cust_obj = Model.customer_info()
                cust_obj.mobile_no = mobile_no
                cust_obj.service_type_id = service_type_id
                cust_obj.save()
                session_id = cust_obj.session_id
                
                ms_payload = {'mobile_no':mobile_no, 'cust_obj': cust_obj, 'session_id':session_id, 'service_type_id': service_type_id}
                self.appbackend.save_mobile_session(ms_payload)   #save in session_map, customer_register, customer_info             
                nq_payload = {'cust_obj': cust_obj, 'session_id':session_id, 'prev_question_id': -2}
                res = self.appbackend.get_next_ques(nq_payload)
                next_ques = res['question_desc']
                next_question_id = res['next_question_id']
                s_payload = {'cust_obj': cust_obj, 'session_id':session_id, 'prev_question_id': 3003, 'next_question_id': next_question_id, 'mobile_no': mobile_no, 'service_type_id': service_type_id} #all other parameters are null
                self.appbackend.save_session_log(s_payload)
                msg = response.message(next_ques)   
            elif verify_now_obj and len(req_data)==1 and req_data.isdecimal() and int(req_data) < 10:           
                verify_now_obj.service_type_id = int(req_data) + 20 #service type_id for coupon codes
                verify_now_obj.save()
                question_desc_eng = cache.get('verifynow_3001')
                question_desc_eng = question_desc_eng.format(service_name=verify_now_obj.service_detail.service_type_name\
                    ,short_url=verify_now_obj.short_url)
                msg = response.message(question_desc_eng)
            else:
                cust_obj = Model.customer_info.objects.filter(mobile_no = mobile_no).last()
                if cust_obj and not cust_obj.mobile_verified:
                    session_id = cust_obj.session_id
                    session_data = {}
                    session_payload = {'cust_obj': cust_obj, 'session_id':session_id, 'mobile_no':mobile_no, "update": ""}

                    self.appbackend.save_mobile_session(session_payload)
                    session_data = self.appbackend.get_session_data(session_payload)
                    if req_data == '':
                        session_data['user_action'] = None
                    elif len(req_data) == 1:
                        if req_data.isdecimal():
                            req_data = int(req_data)
                            session_data['user_action'] = req_data

                            #temporarily stopping employment service
                            if (session_data['prev_question_id'] == 2 or session_data['prev_question_id'] == 50) and req_data > 1 and req_data != 9:
                                session_data['user_action'] = req_data + 1
                        else:
                            raise Exception("ignore")
                    else:
                        session_data['input_data'] = req_data
                        session_data['user_action'] = None
                    if (cust_obj and (session_data['prev_question_id'] == 3004 or session_data['prev_question_id'] == 3005)):           
                        if (session_data['prev_question_id'] == 3004):
                            session_id = cust_obj.session_id
                            cust_obj.service_type_id = self.service_mapping_799[int(req_data)] #service type_id for coupon codes
                            cust_obj.save()

                        elif (session_data['prev_question_id'] == 3005):
                            session_id = cust_obj.session_id
                            cust_obj.service_type_id = self.service_mapping_1499[int(req_data)] #service type_id for coupon codes
                            cust_obj.save()

                        s_payload = {'cust_obj': cust_obj, 'session_id':session_id, 'service_type_id': cust_obj.service_type_id} #all other parameters are null
                        self.appbackend.save_session_log(s_payload)
                        
                        session_id = cust_obj.session_id
                        session_data = {}
                        
                        session_payload = {'cust_obj': cust_obj, 'session_id':session_id, 'mobile_no':mobile_no,"service_type_id":cust_obj.service_type_id}
                        self.appbackend.save_mobile_session(session_payload)
                        session_data = self.appbackend.get_session_data(session_payload)
                        session_data["user_action"] = None
                        session_data["results"] = 24                    

                    is_input_valid = self.appbackend.is_valid_input(session_data) #check input validity
                    if not(is_input_valid):
                        msg = response.message("""Incorrect input provided.
 
*Please give valid input.*""")
                        return HttpResponse(response)
                    action_on_ques = Model.action_on_ques(int(self.appbackend.get_action_on_ques(session_data))).name
                    # print('\naction_on_ques', action_on_ques)
                    action_list = ['_image', '_selfie', 'map_location', 'kyc_check']
                    if any(item in action_on_ques for item in action_list):
                        if 'MediaUrl0' in data:
                            session_data['url'] = data['MediaUrl0']
                        elif 'Latitude' in data:
                            session_data['Latitude'], session_data['Longitude'] = data['Latitude'], data['Longitude']
                        else:
                            msg = response.message("""Incorrect input provided.
 
*Please give valid input.*""")
                            return HttpResponse(response)
                    service_type_id = session_data['service_type_id']       
                    # print("\naction_on_ques-Session_data:",session_data)
                    session_data = self.appbackend.call_func(action_on_ques, session_data)
                    # print("\nresults:-",session_data['results'])
                    if session_data['results'] == 'incorrect_input':          
                        msg = response.message("""Incorrect input provided.
 
*Please give valid input.*""")
                        return HttpResponse(response)
                    session_data['results'] = str(Model.results[session_data['results']].value)
                    #reset value to get correct next questions
                    session_data['service_type_id'] = service_type_id
                    res = self.appbackend.get_next_ques(session_data)
                    # print('next_ques:-', res['question_desc'])
                    # if res['next_question_id'] == 454: # to recheck
                    #     session_data['customer_type'] = 2   
                    #     cust_obj.customer_type = 2
                    #     cust_obj.save()
                    session_data['prev_question_id'] = res['next_question_id'] 
                    payload = {"session_id":session_id} 
                    session_data['service_type_id'] = self.appbackend.get_service_type_id(payload)    
                    if 'question_desc' in session_data:
                        session_data.pop('question_desc')
                    # print("\nsave_session_log-Session_data:",session_data)                    
                    self.appbackend.save_session_log(session_data)
                    # if 'We will contact' in res['question_desc'] and session_data['service_type_id'] == 30:
                    #     res['question_desc'] = ''
                    msg = response.message(res['question_desc'])
                    # if payment is done from session id, mobile verified for candidate and report is not send yet
                    # elif cust_obj and cust_obj.payment_status and cust_obj.mobile_verified and \
                    #     cust_obj.order_set.filter(report_sent_time = None):
                    #     msg = response.message('')
                    #     return HttpResponse(response)
                else:
                    edu_obj = Model.EducationData.objects.filter(mobile_no = mobile_no).exclude(case_status = '1').last()
                    if edu_obj and 'MediaUrl0' in data:
                        self.appbackend.save_edu_doc(data['MediaUrl0'], edu_obj)
                        msg = response.message('')
                    elif not edu_obj:
                        cowin_obj = Model.CowinData.objects.filter(Q(case_status = False), \
                            Q(whatsapp_mobile_no = mobile_no)).last()
                        if 'cowin_' in req_data.lower():
                            res = self.appbackend.initiate_cowin_check(req_data, mobile_no)
                            msg = response.message(res)
                        elif cowin_obj and len(req_data) in (1, 6, 10):
                            res = self.appbackend.get_cowin_details(req_data, cowin_obj)
                            msg = response.message(res)
                        else:
                            msg = response.message("""Incorrect input provided.
 
*Please give valid input.*""")
                    else:
                        msg = response.message("""Incorrect input provided.
 
*Please give valid input.*""")
           # handling time out issue
            end_time = time.time()
            if end_time - start_time > 13:
                send_msg = processor.DB_Processor()
                send_msg.sent_reminder(mobile_no, msg.value)
                msg = response.message('')
                return HttpResponse(response)
            else: 
                return HttpResponse(response)
        except Exception as ex:            
            traceback.print_exc()
            if str(ex) != 'ignore':
                logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
            msg = response.message("""Incorrect input provided.
 
*Please give valid input.*""")
            return HttpResponse(response)     
