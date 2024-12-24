import datetime, time
from django_cron import CronJobBase, Schedule
from django.db.models import Q
import requests
from hv_whatsapp import settings as app_settings
import json
import datetime 
from hv_whatsapp_api import models as Model
from ocr_apis import models as Ex_Model
from promotional_marketing import models as Pr_Model
import pandas as pd
from hv_whatsapp_api import views
from . import check_processor as check_processors
from .whatsapp_backend_api import Whatsapp_backend as apibackend
from .Redis_Processor import RedisDB
from django.utils.timezone import utc
from . import views as apicall
from . import report
from retrying import retry
from. import send_mail as mail
# from ocr_apis.verification_api import Verification as Verify
from datetime import timedelta
import os
import logging
import inspect
import traceback
import sys
import ftplib
import os
import time
import glob

logging.basicConfig(filename="error_log.log")

'''
Scheduler for Criminal Check API hit
'''
class run_crime_record_send_scheduler(CronJobBase):
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'run_crime_record_send_scheduler'    # a unique code

    def do(self):
        print(f'Running run_crime_record_send_scheduler - Time={datetime.datetime.now()}')
        try:
            hv_call = check_processors.BaseCheckProcessor()
            api_url = app_settings.EXTERNAL_API['CRIME_CHECK_URL']
            items = Model.criminal_result.objects.filter(Q(manual_color_code=5) | Q(manual_color_code=0), color_code=3)
            # items.update(manual_color_code=4)
            # for item in items:
            #     item.manual_color_code = 4
            #     item.save()            
            for item in items:
                try:
                    request_sent = item.request_sent
                    rule_engine_result = item.rule_engine_result
                    api_result = item.api_result
                    id = item.id
                    data = self.populate_item(rule_engine_result, api_result, request_sent, id)
                    
                    print("calling the hv site")
                    res = hv_call.post_hv_site(api_url, data)
                    json_str = res.text
                    json_obj = json.loads(json_str)
                    # break
                    if json_obj['StatusCode']!=200:
                        item.manual_color_code = 5
                        item.remark = "getting 500 error on the api call"
                    else:
                        item.manual_color_code = 3
                        item.check_id = json_obj['CheckId']
                        item.remark = "Sent for manual check"
                        # print("record with 200 status code")
                        
                    item.save()
                        
                except Exception as e:
                    item.manual_color_code = 5
                    item.remark = str(e)
                    item.save()
                    print(traceback.print_exc())
                    logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
                    logging.exception((inspect.currentframe().f_code.co_name).upper())
        except Exception as e:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
        
    '''
    create unique check id for each criminal cases
    '''
    def generate_check_id(self, id):
        try:
            # write the logic here to generate the checkid
            # 854074/2019-CCVE-2
            prefix = "{0:0=6d}".format(id)
            year = datetime.datetime.now().year
            final_code = str(prefix)+"/"+str(year)+"-WHATSAPP-CCVE"
            return final_code
        except Exception as e:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            
    '''
    populate all the details for manual
    '''
    def populate_item(self, rule_engine_result, api_result, request_sent, id):
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
            data['details'] = rule_engine_result
            data_final = {}
            data_final['Checkid'] = self.generate_check_id(id)
            data_final['Name'] = request_sent['name']
            data_final['Address'] = request_sent['address']
            data_final['Source'] = 'HV_WHATSAPP'
            data_final['AdditionalData'] = ""
            data_final['VerifiedData1'] = data
            
            return data_final
        except Exception as e:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

'''
Scheduler for Reminder to send reminder to customers for payment and to start
verification process
'''
class send_reminder_scheduler(CronJobBase):
    
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'send_reminder_scheduler'    # a unique code

    def do(self):
        print('send_reminder_scheduler-->' + str(datetime.datetime.now()))        
        try:
            # find batch for reminder_type = payment
            batch = Model.reminder.objects.filter(reminder_type = 0)
            for item in batch:
                time_diff = self.find_time_difference_in_minutes(item.updated_at)
                session_id = item.customer_info.session_id
                cust_model = Model.customer_info.objects.get(session_id = session_id)

                if cust_model.payment_status == 1:
                    continue

                # get package name
                customer_type = cust_model.customer_type
                service_type_id = cust_model.service_type_id
                service_model = Model.service_detail.objects.filter(customer_type = customer_type,service_type_id = service_type_id).last()
                package_name = (service_model.service_type_name).title()

                # change question with package name and time
                ques_desc = "*Gentle Reminder!*\n\nPlease make payment of your *{package}* to continue the background verification process.\n\n*Note:* Payment link will expire within *{time}* minutes."
                if time_diff in range(9,11):
                    ques_desc = ques_desc.replace("{package}",(package_name.replace(".","")).strip()).replace("{time}","20")
                    self.sent_reminder(cust_model.mobile_no,ques_desc)
                
                elif time_diff in range(19,21) and cust_model.payment_status == 0:
                    ques_desc = ques_desc.replace("{package}",(package_name.replace(".","")).strip()).replace("{time}","10")
                    self.sent_reminder(cust_model.mobile_no,ques_desc)
                
                elif time_diff >= 30:
                    Model.reminder.objects.filter(customer_info = session_id).delete()
                else:
                    pass

            # find batch for reminder_type = verification ( This is only for verification through someone else)
            batch = Model.reminder.objects.filter(reminder_type = 1)
            for item in batch:
                time_diff = self.find_time_difference_in_minutes(item.updated_at)
                session_id = item.customer_info.session_id
                lookup_model = Model.customer_lookup.objects.filter(customer_info = session_id).last()
                try:
                    order_obj = Model.order.objects.get(customer_info = session_id)
                    order_id = order_obj.order_id
                except:
                    continue

                # send reminder in 4 hours
                if time_diff in range(4*60,4*60+2):
                    sess_log_model = Model.session_log.objects.get(customer_info = session_id)
                    if sess_log_model.prev_question_id == 60:
                        # desc for requester
                        desc = self.get_reminder_ques_desc('requester', session_id, ques_id = 309)
                        vendor_name = lookup_model.vendor_name
                        candidate_name = lookup_model.candidate_name
                        candidate_mobile = lookup_model.candidate_mobile
                        desc_change1 = desc.replace("{_vendor_}",vendor_name).replace("{_candidate_}",candidate_name).replace("{_candidate_mobile_}",candidate_mobile)
                        self.sent_reminder(lookup_model.vendor_mobile,desc_change1)
                
                # send reminder in 6 hours
                elif time_diff in range(10*60,10*60+2):
                    sess_log_model = Model.session_log.objects.filter(customer_info = session_id).last()
                    if sess_log_model.prev_question_id == 60:
                        # desc for requester
                        desc = self.get_reminder_ques_desc('requester', session_id, ques_id = 309)
                        vendor_name = lookup_model.vendor_name
                        candidate_name = lookup_model.candidate_name
                        candidate_mobile = lookup_model.candidate_mobile
                        desc_change1 = desc.replace("{_vendor_}",vendor_name).replace("{_candidate_}",candidate_name).replace("{_candidate_mobile_}",candidate_mobile)
                        self.sent_reminder(lookup_model.vendor_mobile,desc_change1)

                elif time_diff in range(48*60,48*60+2):
                    time_remain = '24'
                    # desc for candidate
                    desc = self.get_reminder_ques_desc('candidate', session_id, ques_id = 301)
                    vendor_name = lookup_model.vendor_name
                    desc_change1 = desc.replace("{{1}}",vendor_name).replace("{{2}}",order_id).replace("{{3}}",time_remain)
                    self.sent_reminder(lookup_model.candidate_mobile,desc_change1)

                    # desc for requester
                    desc = self.get_reminder_ques_desc('requester', session_id, ques_id = 302)
                    candidate_name = lookup_model.candidate_name
                    desc_change2 = desc.replace("{{1}}",order_id).replace("{{2}}",candidate_name).replace("{{3}}",time_remain)
                    self.sent_reminder(lookup_model.vendor_mobile,desc_change2)

                elif time_diff in range(71*60,71*60+2):
                    # desc for candidate
                    desc = self.get_reminder_ques_desc('candidate', session_id, ques_id = 304)
                    vendor_name = lookup_model.vendor_name
                    desc_change1 = desc.replace("{{1}}",vendor_name).replace("{{2}}",order_id)
                    self.sent_reminder(lookup_model.candidate_mobile,desc_change1)

                    # desc for vendor
                    desc = self.get_reminder_ques_desc('requester', session_id, ques_id = 305)
                    candidate_name = lookup_model.candidate_name
                    desc_change2 = desc.replace("{{1}}",candidate_name).replace("{{2}}",order_id)
                    self.sent_reminder(lookup_model.vendor_mobile,desc_change2)
        
                elif time_diff in range(120*60,120*60+2):
                    views.generate_incomplete_report(order_obj.mobile_no, session_id)
                    Model.reminder.objects.filter(customer_info = session_id).delete()
                    Model.session_map.objects.filter(customer_info = session_id).delete()
                else:
                    pass

            return True
 
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    '''
    get reminder questions
    '''
    def get_reminder_ques_desc(self, custumer_type, session_id, ques_id):
        try:
            # get language_type
            # if custumer_type == 'requester': #check
            #     check_model = Model.customer_info.objects.filter(session_id = session_id).first()
            #     language = check_model.language_type
            # if custumer_type == 'candidate':
            #     check_model = Model.customer_info.objects.filter(session_id = session_id).last()
            #     language = check_model.language_type
            # check_model = Model.customer_info.objects.get(session_id = session_id)
            language = 1
            # get question description
            redis = RedisDB()
            desc = redis.get_question_string(ques_id,language)
            return desc

        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # Find difference between updated time and current time        
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
                    media_url=[url],
                    from_='whatsapp:+14157924931',
                    body=mesg,
                    to='whatsapp:'+mobile
                )
            return ''
        except Exception as ex:
            # print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

# cron scheduler for karza api id check scheduler
class id_check_scheduler1(CronJobBase):

    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'id_check_scheduler1'    # a unique code

    def do(self):
        print('id_check_scheduler1-->' + str(datetime.datetime.now()))
        try:
            # find batch for id_check_status = False
            batch = Model.report_check.objects.filter(id_check_status = False, init_qc_done = True)

            for item in batch:                
                order_id = item.order.order_id
                print('id_check ' + str(datetime.datetime.now()) + ' order_id ' + order_id)
                session_id = item.order.customer_info.session_id
                id_type = item.order.customer_info.id_type
                payload = {"session_id": session_id}
                
                api_obj = Model.api_hit_count.objects.get(order = order_id)
                self.call_id_api = apicall.Views()
                if id_type == '1':
                    if api_obj.anti_captcha >= 6:
                        continue
                    self.call_id_api.get_adhaar_results(payload)
                    break
                elif id_type == '2':
                    if api_obj.dl_api >= 1:
                        continue
                    self.call_id_api.get_dl_results(payload)   
                    break
            return True
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

# cron scheduler for karza api emp check scheduler
class api_call_for_emp_check_scheduler1(CronJobBase):

    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'api_call_for_emp_check_scheduler'    # a unique code

    def do(self):
        print('api_call_for_emp_check_scheduler-->' + str(datetime.datetime.now()))
        try:
            # find batch for emp_check_status = False
            batch = Model.report_check.objects.filter(emp_check_status = False, init_qc_done = True)

            for item in batch:
                order_id = item.order.order_id
                session_id = item.order.customer_info.session_id
                api_obj = Model.api_hit_count.objects.get(order = order_id)                
                self.call_id_api = apicall.Views()

                payload = {"session_id": session_id, 'order_id': order_id}
                if api_obj.emp_api >= 2:
                    continue
                api_obj.emp_api = api_obj.emp_api + 1
                api_obj.save()
                res = self.call_id_api.get_uan_results(payload)
                if res['result'] == True:
                    item.emp_check_status = True
                    item.save()
            return True
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)
    

# cron scheduler for karza api id check scheduler
class api_call_for_crime_check_scheduler(CronJobBase):

    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'api_call_for_crime_check_scheduler'    # a unique code

    def do(self):
        print('api_call_for_crime_check_scheduler-->' + str(datetime.datetime.now()))
        try:
            # find batch for crime_check_status = False
            batch = Model.report_check.objects.filter(crime_check_status = False, init_qc_done = True)

            for item in batch:
                order_id = item.order.order_id
                print('crime_check ' + str(datetime.datetime.now()) + ' order_id ' + order_id)
                session_id = item.order.customer_info.session_id
                api_obj = Model.api_hit_count.objects.get(order = order_id)
                crime_check_model = Model.criminal_result.objects.filter(order = order_id).last()
                
                if crime_check_model == None:
                    print("Criminal API hit---->>>", api_obj.crime_api)
                    payload = {"session_id": session_id}
                    if api_obj.crime_api >= 2 or api_obj.address_parser_api >= 2:
                        print('limit exceed--criminal hit')
                        continue
                    print('crime api --------- hit')
                    self.call_id_api = apicall.Views()
                    self.call_id_api.get_crimecheck_results(payload)
                else:
                    if crime_check_model.remark == "Sent for manual check":
                        pass
                        # print("Sent for manual check")
                    elif crime_check_model.remark == "Manual response received":
                        print("Manual response received")
                        item.crime_check_status = True
                        item.save()
                    else:
                        pass
            print("no items")
            return True
        except Exception as ex:   
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

# cron scheduler for karza api id check scheduler
class generate_report_scheduler(CronJobBase):

    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'generate_report_scheduler'    # a unique code
    
    def do(self):
        print('generate_report_scheduler-->' + str(datetime.datetime.now()))
        try:
            # find batch for send_report = False
            batch = Model.report_check.objects.filter(report_status = '0', init_qc_done = True) 

            for item in batch:
                
                order_id = item.order.order_id
                session_id = item.order.customer_info.session_id
                # check id manual status and update id_check
                id_check = item.id_check_status 
                if id_check:
                    pass
                else:
                    cust_model = Model.customer_info.objects.get(session_id = session_id)

                    if cust_model.id_type == '2':
                        
                        dl_manual = Model.dl_manual_response.objects.filter(order = order_id).last()
                        if dl_manual:
                            dl_lst = []
                            dl_lst.append(dl_manual.dl_number)
                            dl_lst.append(dl_manual.name)
                            dl_lst.append(dl_manual.father_name)
                            dl_lst.append(dl_manual.address)

                            if "" in dl_lst or "na" in dl_lst or "Na" in dl_lst or "NA" in dl_lst:
                                id_check = False
                            else:
                                # set the report data into database for dl manual cases
                                # session_id = item.session_id # we have commented this due to issue
                                session_id = session_id
                                payload = {"session_id": session_id}
                                self.call_id_api = apicall.Views()
                                self.call_id_api.get_dl_manual_results(payload)  

                                # save the id check status
                                id_check = True
                                item.id_check_status = True
                                item.save()

                crime_check = item.crime_check_status
                emp_check = item.emp_check_status
                # print('id_check', id_check)
                # print('crime_check', crime_check)
                # print('emp_check', emp_check)
                cust_obj = Model.customer_info.objects.get(session_id=session_id)
                service_type_id = cust_obj.service_type_id
                # get report json
                if service_type_id == 2:
                    if id_check and crime_check and emp_check:
                        payload = {}
                        payload['session_id'] = session_id
                        payload['order_id'] = order_id

                        # obj_report = report.Report()
                        # final_report_data = obj_report.create_report(payload)
                        cust_obj = Model.customer_info.objects.get(session_id=session_id)
                        
                        if cust_obj.customer_type == '1':                        
                            views.generate_report(cust_obj.mobile_no, session_id)
                        else:
                            look_obj = Model.customer_lookup.objects.filter(customer_info=session_id).last()
                            views.generate_report(look_obj.vendor_mobile, session_id)
                        # item.send_report = False
                        # item.save()
                else:
                    if id_check and crime_check:
                        payload = {}
                        payload['session_id'] = session_id
                        payload['order_id'] = order_id

                        # obj_report = report.Report()
                        # final_report_data = obj_report.create_report(payload)
                        cust_obj = Model.customer_info.objects.get(session_id=session_id)
                        
                        if cust_obj.customer_type == '1':                        
                            views.generate_report(cust_obj.mobile_no, session_id)
                        else:
                            look_obj = Model.customer_lookup.objects.filter(customer_info=session_id).last()
                            views.generate_report(look_obj.vendor_mobile, session_id)
                    elif id_check and crime_check == None: #for know the identity and KYC package
                        payload = {}
                        payload['session_id'] = session_id
                        payload['order_id'] = order_id

                        # obj_report = report.Report()
                        # final_report_data = obj_report.create_report(payload)
                        cust_obj = Model.customer_info.objects.get(session_id=session_id)
                        
                        if cust_obj.customer_type == '1':                        
                            views.generate_report(cust_obj.mobile_no, session_id)
                        else:
                            look_obj = Model.customer_lookup.objects.filter(customer_info=session_id).last()
                            views.generate_report(look_obj.vendor_mobile, session_id)
            return True
        except Exception as ex:     
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


# cron scheduler for send report scheduler
# class api_call_for_send_report_scheduler(CronJobBase):

#     GAP_SEC = 0
#     schedule = Schedule(run_every_mins=GAP_SEC)
#     code = 'api_call_for_send_report_scheduler'    # a unique code

#     def do(self):
#         # print("Running api_call_for_send_report_scheduler")
#         try:
#             # find batch for emp_check_status = False
#             batch = Model.report_check.objects.filter(send_report = True)

#             for item in batch:
#                 # print('=======',item)
#                 # session_id = (item.session_id).replace('__generate', '').strip()
#                 if '__done' in item.session_id:
#                     continue
#                 cust_obj = Model.customer_info.objects.filter(session_id = (item.session_id).replace('__generate', '').strip()).last()

#                 if cust_obj.customer_type == '1':
#                     mobile_no = cust_obj.mobile_no
#                 elif cust_obj.customer_type == '3':

#                     lookup_obj = Model.customer_lookup.objects.filter(customer_info = (item.session_id).replace('__generate', '').strip()).last()
#                     mobile_no = lookup_obj.vendor_mobile

#                 #     # if session is 24hrs old then send msg
#                 #     mob_obj1 = Model.session_map.objects.filter(mobile_no = mobile_no).first()
#                 #     if mob_obj1:
#                 #         last_time = (mob_obj1.updated_at).replace(tzinfo=None)
#                 #         current_time = datetime.datetime.now().replace(tzinfo=None)

#                 #         time_diff = (current_time - last_time)
#                 #         total_seconds = time_diff.total_seconds()
#                 #         minutes = total_seconds/60
#                 #         hours = int(minutes/60)

#                 #         if hours > 24:
#                 #             desc = self.get_ques_desc(mob_obj1.session_id, ques_id = 307)
#                 #             self.sent_notification(mobile_no,desc)
#                 #             continue
                    
#                 print('sending report----------')
#                 views.send_report(mobile_no, item.session_id)
#             return True
#         except Exception as ex:
#             print(traceback.print_exc())
#             logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
#             logging.exception((inspect.currentframe().f_code.co_name).upper())
#             return str(ex)

    # Send reminder to particular whatsapp number
    def sent_notification(self,mobile, mesg, url=None):
        try:
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
            else:
                message = client.messages \
                    .create(
                        media_url=[url],
                        from_='whatsapp:+14155238886',
                        body=mesg,
                        to='whatsapp:'+mobile
                    )
            return ''
        except Exception as ex:
            # print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    def get_ques_desc(self,session_id,ques_id):
        try:
            # get language_type
            check_model = Model.session_log.objects.get(customer_info = session_id)
            language = check_model.language_type

            # get question description
            redis = RedisDB()
            desc = redis.get_question_string(ques_id,language)
            return desc

        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

# cron scheduler for payment failure messages
class api_call_mistmatch_payment_scheduler(CronJobBase):

    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'api_call_mistmatch_payment_scheduler'    # a unique code
    
    def do(self):
        print('api_call_mistmatch_payment_scheduler-->' + str(datetime.datetime.now()))
        try:
            import razorpay
            key = app_settings.RAZORPAY_KEYS["RAZORKEY"]
            secret = app_settings.RAZORPAY_KEYS["RAZORSECRET"]

            client = razorpay.Client(auth=(key,secret))

            # create payload for payment fetch
            payload = {}
            payload["count"] = 100

            to_sec = datetime.datetime.now()
            from_sec = int((to_sec-datetime.datetime(1970,1,1)).total_seconds())
            
            payload["from"] = from_sec - 1800 # last 30 minutes data

            resp = client.payment.fetch_all(data = payload)
            items = resp["items"]

            #match payment details
            required_payment = [74900, 42400, 89900, 149900, 179900]
            for item in items:
                # print('item',item)
                if item["amount"] in required_payment and (item["status"] == "captured" or item["status"] == "authorized"):
                    transaction_model = Model.transaction_log.objects.filter(transaction_id = item["id"])
                    if transaction_model.count() == 0:
                        # send mail
                        subject = "Transaction Not Found"
                        content = '''<html xmlns="http://www.w3.org/1999/xhtml" ><head><title>Candidate Details</title><style>body {font-family:Verdana; font-size:10px;}a{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#105496;text-decoration:none;background-color:Transparent;float:left;}.a:hover{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#000000;text-decoration:none;background-color:Transparent;float:left;}.a:active{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#000000;text-decoration:none;background-color:Transparent;float:left;}</style></head><body><table width="600" border="1" cellpadding="10" cellspacing="1" bordercolor="#666666"><tr><td align="Center" height="50" width="485"><img alt="helloverify" src="https://helloverify.com/Content/Images/uploaded/logo.jpg" /><br/>(This is an auto generated email, kindly do not revert)</td></tr><tr><td><br/><br/>'''+\
                        "Transaction id: "+item["id"]+"<br/>"\
                            "Amount: "+str(item["amount"])+"<br/>"\
                                "Contact: "+item["contact"]+"<br/>"\
                                    "Email: "+item["email"]+"<br/><br/>"\
                        '''<br/><br/>Regards<br/>Payment Mismatch Scheduler<br/></td></tr><tr><td style='font-size:11px;font-family:Arial,Helvetica,sans-serif;text-align:left;color:#454545;line-height:20px;text-decoration:none;vertical-align:middle;line-height:18px'>In case of any further queries kindly write to us at hellov@helloverify.com. We will be happy to help.</td></tr></table></body></html>'''
                        mail_process = mail.Send_Email()
                        mail_process.process(subject,content)  
                    else:
                        continue

            return True
        except Exception as ex:   
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

# cron scheduler for send error_log
class api_call_for_error_log_scheduler(CronJobBase):
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'api_call_for_error_log_scheduler'    # a unique code
    
    def do(self):
        print('api_call_for_error_log_scheduler-->' + str(datetime.datetime.now()))
        try:
            if "<----------" in open("/home/hello/proj_id_check/fintech_backend/error_log.log").read():
                content = ""
                f = open("/home/hello/proj_id_check/fintech_backend/error_log.log",'r')
                for line in f:
                    content = content + line + '\n'
                f.close()
                msg_index = content.find('<-----')
                content = content[msg_index:]
                subject = "error_log"
                mail_process = mail.Send_Email()
                mail_process.process(subject,content)                  
                return True
            else:
                return True
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)



# cron scheduler for send error_log
class add_promotional_data(CronJobBase):
    GAP_SEC = 1
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'add_promotional_data'    # a unique code
    
    def do(self):
        print('add_promotional_data-->' + str(datetime.datetime.now()))
        try:
            pending_data = Pr_Model.PromotionalData.objects.filter(is_data_imported=False).last()
            if pending_data:
                data_csv = pending_data.csv_file.path
                all_data = pd.read_csv(data_csv)
                all_data = all_data.to_dict('records')
                for data in all_data:
                    try:
                        if pending_data.send_all_at_once:
                            Pr_Model.PromotionalMessageTracker.objects.create(mobile_no=data.get("mobile_num"),message_code=data.get("message_code",5000),from_file=pending_data,send_force=True)
                            pending_data.message_sent = pending_data.message_sent + 1
                            pending_data.save()
                        else:
                            Pr_Model.PromotionalMessageTracker.objects.create(mobile_no=data.get("mobile_num"),message_code=data.get("message_code",5000),from_file=pending_data)
                    except Exception as ex:
                        print(traceback.print_exc())
                        logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
                        logging.exception((inspect.currentframe().f_code.co_name).upper())
                pending_data.is_data_imported = True
                pending_data.save()
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


# cron scheduler for send error_log
class send_promotional_message(CronJobBase):
    # RUN_AT_TIMES = ['21:00']  # Run at 9 PM
    # schedule = Schedule(run_at_times=RUN_AT_TIMES)

    GAP_SEC = 10
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'send_promotional_message'    # a unique code
    
    def do(self):
        print('send_promotional_message-->' + str(datetime.datetime.now()))
        try:
            pending_data = Pr_Model.PromotionalData.objects.filter(is_data_imported=True,send_all_at_once=False)
            for data in pending_data:
                pending_message = Pr_Model.PromotionalMessageTracker.objects.filter(is_message_sent_once=False,from_file=data)[:data.batch_size]
                for message in pending_message:
                    message.send_force = True
                    message.save()
                    data.message_sent = data.message_sent + 1
                    data.save()
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

        

#leads followup message scheduler
class msg_incomplete_transactions(CronJobBase):
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'msg_incomplete_transactions'    # a unique code          
    
    def do(self):
        print('msg_incomplete_transactions-->' + str(datetime.datetime.now()))
        try:
            time_threshold = datetime.datetime.now() - timedelta(hours=9)
            from datetime import date
            yesterday = date.today() - timedelta(days = 130)
            
            verify_now_batch = Model.VerifyNow.objects.filter(updated_at__day=yesterday.day, transaction_captured=False, service_type_id=0)
            verify_now_items = list(verify_now_batch.values_list('mobile_no', flat=True).distinct())
            
            ed_batch = Model.EducationData.objects.all()
            ed_items = list(ed_batch.values_list('mobile_no', flat=True).distinct())
            items = [i for i in verify_now_items if i not in ed_items]

            sound_symbol = "🔊"
            # ques_desc = Model.question_master.objects.get(question_id = 308)
            ques_desc = Model.question_master.objects.get(question_id = 1111)
            ques_desc = ques_desc.question_desc_eng.format(sound1=sound_symbol,sound2=sound_symbol)
            for mobile_no in items:
                self.sent_reminder(mobile_no, ques_desc)
            Model.customer_info.objects.filter(
                (Q(payment_status = False) & Q(updated_at__lt = time_threshold)) | \
                    (Q(payment_status = True) & Q(updated_at__lt = time_threshold) & \
                        Q(mobile_no = '+919205264013') & ~Q(session_id = 4873))).delete()
            Model.customer_info.objects.filter(
                (Q(payment_status = False) & Q(updated_at__lt = time_threshold)) | \
                    (Q(payment_status = True) & Q(updated_at__lt = time_threshold) & \
                        Q(mobile_no = '+917532973604') & ~Q(session_id = 11640))).delete()
            Model.customer_info.objects.filter(
                (Q(payment_status = False) & Q(updated_at__lt = time_threshold)) | \
                    (Q(payment_status = True) & Q(updated_at__lt = time_threshold) & \
                        Q(mobile_no = '+919928927887') & ~Q(session_id = 11640))).delete()
            return True
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
                    media_url=[url],
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



#leads followup message scheduler for Cart_Abandonment
class msg_for_cart_abandonment_users(CronJobBase):
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'msg_for_cart_abandonment_users'    # a unique code
    
    def do(self):
        print('msg_for_cart_abandonment_users-->' + str(datetime.datetime.now()))
        try:
            from datetime import date
            yesterday = date.today() - timedelta(days = 30)
            verify_now_batch = Model.VerifyNow.objects.filter(Q(updated_at__day=yesterday.day) & Q(transaction_captured=False) & ~Q(service_type_id = 0))
            verify_now_items = list(verify_now_batch.values_list('mobile_no', flat=True).distinct())
            ed_batch = Model.EducationData.objects.all()
            ed_items = list(ed_batch.values_list('mobile_no', flat=True).distinct())
            items = [i for i in verify_now_items if i not in ed_items]

            nanny_symbol = "👩‍👧‍👦"
            car_symbol = "🚗"
            house_symbol = "🏠"
            msg = Model.question_master.objects.filter(question_id=1112).last()
            msg = msg.question_desc_eng.format(service="verify")
            ques_desc = msg + nanny_symbol+car_symbol+house_symbol
    
            for mobile_no in items:
                self.sent_reminder(mobile_no, ques_desc)
            
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
                    media_url=[url],
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



#leads followup message scheduler
class send_education_check_msgs(CronJobBase):
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'send_education_check_msgs'    # a unique code
    
    def do(self):
        print('send_education_check_msgs-->' + str(datetime.datetime.now()))
        try:
            batch = Model.EducationData.objects.filter(message_sent = False)
            if batch:
                for item in batch:                
                    ques_desc = Model.question_master.objects.get(question_id = 1001)
                    final_ques_desc = self.update_question(ques_desc.question_desc_eng, 1001, item)                    
                    sid = self.sent_reminder(item.mobile_no, final_ques_desc)
                    item.last_message_sid = sid
                    item.message_sent = True
                    item.save()
                # self.download_doc()
            batch = Model.EducationData.objects.filter(case_status = '0', doc_reminder__gt = 0) #pending
            if batch:
                for item in batch:
                    time_diff = self.find_time_difference_in_minutes(item.created_at)
                    # print('pending reminder time_diff-------->', time_diff)
                    # print('mobile_no-------->', item.mobile_no)                    
                    if time_diff > 48*60 and item.doc_reminder == 1:
                        print('mobile_no of cases older than 48 hours -->', item.mobile_no)
                        ques_desc = Model.question_master.objects.get(question_id = 1002)
                        final_ques_desc = self.update_question(ques_desc.question_desc_eng, 1002, item, "24")
                        sid = self.sent_reminder(item.mobile_no, final_ques_desc)
                        item.doc_reminder = item.doc_reminder - 1
                        item.last_message_sid = sid
                        item.save()
                    elif time_diff > 24*60 and item.doc_reminder == 2:
                        print('mobile_no of cases older than 24 hours -->', item.mobile_no)
                        ques_desc = Model.question_master.objects.get(question_id = 1002)
                        final_ques_desc = self.update_question(ques_desc.question_desc_eng, 1002, item, "48")
                        sid = self.sent_reminder(item.mobile_no, final_ques_desc)
                        item.doc_reminder = item.doc_reminder - 1
                        item.last_message_sid = sid
                        item.save()
            batch = Model.EducationData.objects.filter(Q(case_status = '3') | Q(case_status = '4') | Q(case_status = '5'), insuff_reminder__gt = 0) #insuff
            if batch:
                for item in batch:
                    time_diff = self.find_time_difference_in_minutes(item.insuff_time)
                    # print('time_diff-------->', time_diff)
                    # print('mobile_no-------->', item.mobile_no)
                    if item.insuff_reminder == 3 or \
                        (time_diff in range(24*60, 24*60+16) and item.insuff_reminder == 2) or \
                            (time_diff in range(48*60, 48*60+16) and item.insuff_reminder == 1):
                        if item.case_status == '5':
                            ques_desc = Model.question_master.objects.get(question_id = 1004)
                            final_ques_desc = self.update_question(ques_desc.question_desc_eng, 1004, item)
                        else:                    
                            ques_desc = Model.question_master.objects.get(question_id = 1003)
                            final_ques_desc = self.update_question(ques_desc.question_desc_eng, 1003, item)                    
                        sid = self.sent_reminder(item.mobile_no, final_ques_desc)
                        item.insuff_reminder = item.insuff_reminder - 1
                        item.last_message_sid = sid
                        item.save()
            #clease insuff @oni if new document added by candidate
            # batch = Model.EducationData.objects.filter(insuff_oni_update = True, case_status = '2')
            # if batch:
            #     for item in batch:
            #         #hit api and if status @oni is successfully updated
            #         item.insuff_oni_update = False
            #         item.save()                   
            return True
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)
    

    def update_question(self, ques_desc, ques_id, edu_obj, time_remain='1'):
        try:
            unique_id = '*'+edu_obj.unique_id+'*'
            name = '*'+edu_obj.name+'*'

            if ques_id == 1001:
                final_ques_desc = ques_desc.replace("{{1}}", unique_id)
                if edu_obj.tenth == 'Yes' and edu_obj.twelveth == 'Yes':
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*10th and 12th*')
                elif edu_obj.twelveth == 'Yes':
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*12th*')
                else:
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*10th*')
                final_ques_desc = final_ques_desc.replace("{{3}}", name)
            elif ques_id == 1002: 
                final_ques_desc = ques_desc.replace("{{1}}", unique_id)
                if edu_obj.tenth == 'Yes' and edu_obj.twelveth == 'Yes':
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*10th and 12th*')
                else:
                    final_ques_desc = final_ques_desc.replace("{{2}}", '*10th*')
                final_ques_desc = final_ques_desc.replace("{{3}}", name)
                hours = time_remain
                final_ques_desc = final_ques_desc.replace("{{4}}", hours)
            elif ques_id == 1003:
                final_ques_desc = ques_desc.replace("{{1}}", unique_id)
                if edu_obj.insuff_10th_remark:
                    final_ques_desc = final_ques_desc.replace("{{2}}", edu_obj.insuff_10th_remark)
                elif edu_obj.insuff_12th_remark:
                    final_ques_desc = final_ques_desc.replace("{{2}}", edu_obj.insuff_12th_remark)
                final_ques_desc = final_ques_desc.replace("{{3}}", name)
                hours = str(int(72 - ((datetime.datetime.now() - edu_obj.insuff_time).total_seconds())//(60 * 60)))
                final_ques_desc = final_ques_desc.replace("{{4}}", hours)
            elif ques_id == 1004:                
                final_ques_desc = ques_desc.replace("{{1}}", unique_id)
                if edu_obj.insuff_10th_remark and edu_obj.insuff_12th_remark:
                    final_ques_desc = final_ques_desc.replace("{{2}}", edu_obj.insuff_10th_remark)
                    final_ques_desc = final_ques_desc.replace("{{4}}", edu_obj.insuff_12th_remark)
                final_ques_desc = final_ques_desc.replace("{{3}}", name)
                final_ques_desc = final_ques_desc.replace("{{5}}", name)
                hours = str(int(72 - ((datetime.datetime.now() - edu_obj.insuff_time).total_seconds())//(60 * 60)))
                final_ques_desc = final_ques_desc.replace("{{6}}", hours)
            # print('final_ques_desc', final_ques_desc)
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
            return message.sid
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

#leads followup message scheduler
class send_cowin_mesg(CronJobBase):
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'send_cowin_mesg'    # a unique code
    
    def do(self):
        print('send_cowin_mesg-->' + str(datetime.datetime.now()))
        try:
            batch = Model.CowinData.objects.filter(case_status = True)
            if batch:                
                for item in batch:
                    time_diff = self.find_time_difference_in_minutes(item.updated_at)

                    if item.cowin_mobile_no and (item.reminder_count == 2 and time_diff > 2) or \
                        (item.reminder_count == 1 and time_diff > 4):                        
                        ques = apibackend.get_cowin_details(item.whatsapp_mobile_no[3:], item)
                        self.sent_reminder(item.whatsapp_mobile_no, ques)
                        
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # Send reminder to particular whatsapp number
    def sent_reminder(self, mobile, mesg, url=None):
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
            return message.sid
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
# cron scheduler to send reports and invoices from server to ftp server every 1st day of a month
# class send_report_to_ftp_scheduler(CronJobBase):

#     GAP_SEC = 0
#     schedule = Schedule(run_every_mins=GAP_SEC)
#     code = 'send_report_to_ftp_scheduler'    # a unique code

#     def do(self):
#         print("Running send_report_to_ftp_scheduler")

#         try:
#             host = "203.92.45.235"
#             # host = "192.168.2.201" #local ip
#             port = 21
#             user = "Whatsapp"
#             password = "Welcome@886"
#             interval = 0.05

#             # FTP Connection
#             ftp = ftplib.FTP()
#             ftp.connect(host,port)
#             ftp.login(user, password)
#             print("Login Successful")

#             # call upload file
#             self.uploadFile(ftp)
            
#             return True
#         except Exception as ex:
#             print(traceback.print_exc())
#             logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
#             logging.exception((inspect.currentframe().f_code.co_name).upper())
#             return str(ex)

#     def uploadFile(self,ftp):
#         try:
#             self.ftp = ftp
#             report_lst, invoice_lst  = self.get_report_invoice_file_list()

#             if report_lst:
#                 destination = "/whatsapp_report"
#                 self.ftp.cwd(destination)
#                 for fil in report_lst:
#                     file_name = fil.split("/")[-1]
#                     print(file_name)
#                     if os.path.isfile(fil):
#                         fh = open(fil, 'rb')
#                         self.ftp.storbinary(f'STOR {file_name}', fh)
#                         fh.close()
#                         os.remove(fil)
#                     else:
#                         print("Source File does not exist"+file_name)

#             if invoice_lst:
#                 destination = "/whatsapp_invoice"
#                 self.ftp.cwd(destination)
#                 for fil in invoice_lst:
#                     file_name = fil.split("/")[-1]
#                     print(file_name)
#                     if os.path.isfile(fil):
#                         fh = open(fil, 'rb')
#                         self.ftp.storbinary(f'STOR {file_name}', fh)
#                         fh.close()
#                         os.remove(fil)
#                     else:
#                         print("Source File does not exist"+file_name)

#             self.ftp.close()
#         except Exception as ex:
#             print("Error: File could not be uploaded ")
#             print(traceback.print_exc())
#             logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
#             logging.exception((inspect.currentframe().f_code.co_name).upper())
#             return str(ex)


    def get_report_invoice_file_list(self):
        try:
            server_file_loc = "/home/hello/proj_id_check/fintech_backend/static/reports/"
            file_list = glob.glob(server_file_loc+"*.pdf")
            report_lst = []
            invoice_lst = []
            for file_path in file_list:
                a = time.time()
                b = os.path.getmtime(file_path)
                if (((a - b)/60)/60/24) > 30:
                    file_name = file_path.split("/")[-1]
                    if 'invoice' in file_name.lower():
                        invoice_lst.append(file_path)
                    else:
                        report_lst.append(file_path)

            return report_lst, invoice_lst

        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

# class hv_light_cases(CronJobBase):
#     GAP_SEC = 0
#     schedule = Schedule(run_every_mins=GAP_SEC)
#     code = 'hv_light_cases'    # a unique code
    
#     def do(self):
#         print('hv_light_cases-->' + str(datetime.datetime.now()))
#         try:
#             rep_obj = Ex_Model.report_check.objects.filter(is_completed = False, retry_count__gt = 0)
#             for item in rep_obj:
#                 item.retry_count = item.retry_count - 1
#                 final_res = {}
#                 claimed_data = json.loads(item.claimed_data)
#                 final_res['info'] = claimed_data
#                 if item.id_check == False:                    
#                     status = Verify().id_check(claimed_data)
#                     if status:                        
#                         item.id_check = True
#                 if item.crime_check == False:
#                     status, res = Verify().crime_check(claimed_data)
#                     if status:
#                         item.crime_check = True
#                         item.crime_res = json.dumps(res)
#                 if item.emp_check == False:
#                     status, res = Verify().emp_check(claimed_data)
#                     if status:
#                         item.emp_check = True
#                         item.emp_res = json.dumps(res)
#                 if item.id_check == False or item.crime_check == False or item.emp_check == False:
#                     print('few checks are still pending')      
#                 elif item.id_check != False and item.crime_check != False and item.emp_check != False:      
#                     if item.id_check:
#                         final_res['is_match'] = True
#                     if item.crime_check:
#                         final_res['info']['crime'] = json.loads(item.crime_res)
#                     if item.emp_check:
#                         final_res['info']['emp'] = json.loads(item.emp_res)
#                     patch_type = True if final_res['info'].get('user_id', None) else False
#                     str_final_res = json.dumps(final_res)
#                     item.final_res = str_final_res
#                     item.is_completed = True
#                     self.submit_result(str_final_res, patch_type)
#                     print('Response patched successfully')
#                 item.save()
#             return True
#         except Exception as ex:     
#             print(traceback.print_exc())
#             logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
#             logging.exception((inspect.currentframe().f_code.co_name).upper())
#             return str(ex)
 
#     def submit_result(self, str_final_res, patch_type):
#         try:
#             if patch_type:
#                 url = app_settings.EXTERNAL_API['SOCIALTICK_URL']+"api/verify-people/hv_data/doc-submit"
#             else:
#                 url = app_settings.EXTERNAL_API['SOCIALTICK_URL']+"api/verify-people/hv_data/submit"
#             res = requests.patch(url=url, data=str_final_res, headers={"Content-Type": "application/json" })
#             print(res.text)
#             return True
#         except Exception as ex:
#             print(traceback.print_exc())
#             logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
#             logging.exception((inspect.currentframe().f_code.co_name).upper())
#             return str(ex)

#whatsapp_file_backupscheduler
class whatsapp_file_backup(CronJobBase):
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'whatsapp_file_backup'    # a unique code
    
    def do(self):
        print('whatsapp_file_backup-->' + str(datetime.datetime.now()))
        try:
            views.edu_data_backup()
            views.ids_data_backup()
            return True
        except Exception as ex:     
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

'''
Scheduler for Reminder to send reminder to verify now customers for payment
'''
class razorpay_reminder_scheduler(CronJobBase):
    
    GAP_SEC = 0
    schedule = Schedule(run_every_mins=GAP_SEC)
    code = 'razorpay_reminder_scheduler'

    def do(self):
        print('razorpay_reminder_scheduler-->' + str(datetime.datetime.now()))        
        try:
            # find batch for reminder_type = payment
            batch = Model.VerifyNow.objects.filter(is_redemption_pin_shared=False, is_session_expired=True, service_type_id__gt=0, is_active=True)
            for item in batch:
                time_diff = self.find_time_difference_in_minutes(item.updated_at)
                if time_diff == 10 or time_diff == 20:
                    package_name = (item.service_detail.service_type_name).title().replace(".", "")
                    ques_desc = f"*Gentle Reminder!*\n\nPlease make payment of your *{package_name}* to continue the background verification process.\n\n{item.short_url}\n\n*Note:* Payment link will expire within *{30-time_diff}* minutes."
                    self.sent_reminder(item.mobile_no,ques_desc)
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    # Find difference between updated time and current time        
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
            return message.sid
        except Exception as ex:
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

class IVRCallingSchedulers(CronJobBase):
    RUN_AT_TIMES = ['21:00']  # Run at 9 PM
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'ivr_calling_for_complete_process'
    
    def do(self):
        from ivr_model.views import ivr_calling_to_complete_process
        print('ivr_calling_for_complete_process-->' + str(datetime.datetime.now()))
        try:
            ivr_calling_to_complete_process()
            return True
        except Exception as ex:    
            print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)    
            