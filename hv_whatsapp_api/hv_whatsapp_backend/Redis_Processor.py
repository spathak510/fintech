import json
import redis
import collections
#from . import db_base_local
from hv_whatsapp_api import models as Model
from hv_whatsapp import settings as app_settings

import logging
import inspect
from datetime import datetime
import traceback
from django.core.cache import cache
import time
logging.basicConfig(filename="error_log.log")

# CURSOR DB
# CURSOR = db_base_local.cnx.cursor()

# Redis Object
# R_SERVER = redis.Redis("localhost")

class RedisDB():

    '''
    get data from table based on session id
    '''
    def get_data_by_session_id(self, session_id):

        try:
            row = Model.session_map.objects.filter(customer_info = session_id).last()
            return row
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    get question string from question master
    Input = question_id, language_type
    Output = question descreption in either Englis or Hindi
    '''
    def get_question_string(self,question_id, language_type):

        try:
            key = "ques_id_" + str(question_id)
            cached_data = cache.get(key)

            if cached_data:
                if language_type == 1: # English
                    question = cached_data[0]
                    question = question.replace('\r','\n')

                elif language_type == 2: # Hindi
                    question = cached_data[1]
                    question = question.replace('\r','\n')
                return question

            ques_model = Model.question_master.objects.get(question_id = question_id)
            value = [ques_model.question_desc_eng, ques_model.question_desc_hindi]

            # set cache key value
            cache.set(key, value, None)

            # Select question language
            if language_type == 1: # English
                question = ques_model.question_desc_eng
                question = question.replace('\r','\n')

            elif language_type == 2: # Hindi
                question = ques_model.question_desc_hindi
                question = question.replace('\r','\n')
            return question
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    get next question id from the mapping tables
    Input = payload(session_id,customer_type,language_type,prev_question,user_action,results,service_type)
    Output = results(mobile, question)
    '''
    def get_next_question_from_redis(self,payload):

        try:
            
            # On HelloV only
            session_id = payload["session_id"]
            prev_question_id = payload["prev_question_id"]

            if prev_question_id == -1:
                question_string = self.get_question_string(0, 1)
                # Prepare results
                results = {
                    "session_id": session_id,
                    "next_question_id": 0,
                    "question_desc": question_string
                }
                return True, results

            if prev_question_id == -2:
                question_string = self.get_question_string(3003, 1)
                # Prepare results
                results = {
                    "session_id": session_id,
                    "next_question_id": 0,
                    "question_desc": question_string
                }
                return True, results

            # data from payload
            session_id = payload["session_id"]
            prev_question_id = payload["prev_question_id"]
            user_action = payload["user_action"]
            service_type_id = payload["service_type_id"]
            results = payload["results"]
            customer_type = int(payload['customer_type'])
            language_type = payload['language_type']
            
            # cache implementation

            if user_action == None:
                key = "nques_id_" + str(service_type_id) +"_"+ str(prev_question_id) +"_"+ str(results)
            else:
                key = "nques_id_" + str(service_type_id) +"_"+ str(prev_question_id) +"_"+ str(user_action) +"_"+ str(results)
            
            cached_data = cache.get(key)

            if cached_data:
                next_question = cached_data
                # get question string from question master table
                question_string = self.get_question_string(next_question, language_type)

                # Prepare results
                results = {
                    "session_id": session_id,
                    "next_question_id": next_question,
                    "question_desc": question_string
                }
                return True, results

            #--------------------------End Cache---------------------------------#
            # set key to null for new key
            
            if (customer_type == 1 or prev_question_id == 1 or prev_question_id == 401) and prev_question_id != 50: # myself
                
                if user_action == None:
                    com_model = Model.communication_myself.objects.filter(prev_question_id = prev_question_id,results = results,service_type_id = service_type_id).last()
                else:
                    com_model = Model.communication_myself.objects.filter(prev_question_id = prev_question_id,results = results,service_type_id = service_type_id, user_action = user_action).last()
    
                next_question = com_model.next_question_id

            else:
                if user_action == None:
                    com_model = Model.communication_someoneelse.objects.filter(prev_question_id = prev_question_id,results = results,service_type_id = service_type_id).last()
                else:
                    com_model = Model.communication_someoneelse.objects.filter(prev_question_id = prev_question_id,results = results,service_type_id = service_type_id, user_action = user_action).last()
    
                next_question = com_model.next_question_id

            # get question string from question master table
            question_string = self.get_question_string(next_question, language_type)

            # Prepare results
            results = {
                "session_id": session_id,
                "next_question_id": next_question,
                "question_desc": question_string
            }
            
            # set cache key value
            cache.set(key, next_question, None)
            return True, results

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

    '''
    get session id from table using mobile number
    Input = mobile
    Output = session id
    '''
    def get_session_id_from_redis(self, mobile_no):
        try:
            results = {}
            mob_sess = Model.session_map.objects.filter(mobile_no = mobile_no).last()

            if mob_sess:
                session_id = mob_sess.customer_info

                results = {
                    "mobile_no":mobile_no,
                    "session_id":session_id
                }
                #printresults)
                return True, results
            else:
                return False, results

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

    '''
    get action on question from mapping table
    Input = payload (prev_question, user_action, service_type_id, session_id)
    Output = action_on_question
    '''
    def get_action_on_ques_from_redis(self, payload):
        try:
            # data from payload
            session_id = payload["session_id"]
            prev_question_id = payload["prev_question_id"]
            user_action = payload["user_action"]
            service_type_id = payload["service_type_id"]
            customer_type = int(payload["customer_type"])

            # Cache Implementation
            key = "action_id_" + str(service_type_id) +"_"+ str(prev_question_id) +"_"+ str(user_action)
            cached_data = cache.get(key)

            if cached_data:
                action_on_ques = cached_data

                results = {
                    "session_id":session_id,
                    "action_on_ques":action_on_ques
                }
                return True, results

            #------------------------End Cache-------------------------------#
            if customer_type == 1: # myself
                com_model = Model.communication_myself.objects.filter(prev_question_id = prev_question_id, service_type_id = service_type_id, user_action = user_action).last()

            else: # someone else
                com_model = Model.communication_someoneelse.objects.filter(prev_question_id = prev_question_id, service_type_id = service_type_id, user_action = user_action).last()

    
            # select action_on_question
            action_on_ques = com_model.action_on_ques

            results = {
                "session_id":session_id,
                "action_on_ques":action_on_ques
            }

            # set cache key value
            cache.set(key, action_on_ques, None)
            return True, results

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False, None

    '''
    insert and update session id for number
    Input = mobile,session_id,language_type, customer_type
    Output = True (tables created successfully)
    '''
    def insert_update_session_map(self, payload):

        try:
            if "mobile_no" in payload and "session_id" in payload and 'service_type_id' not in payload:
                data = {
                    "mobile_no": payload["mobile_no"],
                    "session_id": payload["session_id"],
                    "service_type_id": 0,
                }
                
                # update row
                mob_sess = Model.session_map.objects.filter(mobile_no = data['mobile_no']).last()

                if mob_sess is None:
                    mob_sess.mobile_no = data["mobile_no"]
                    mob_sess.customer_info = data["session_id"]
                    mob_sess.service_type_id = 0
                    mob_sess.save()

                else:
                    mob_sess.customer_info = data["session_id"]
                    mob_sess.service_type_id = 0
                    mob_sess.save()

            elif "session_id" in payload and payload["service_type_id"] > 0:
                # update row
                mob_sess = Model.session_map.objects.get(customer_info = payload["session_id"])
                mob_sess.service_type_id = payload["service_type_id"]
                mob_sess.save()

            elif "session_id" in payload and payload["service_type_id"] == 0 and payload["user_action"] == 0:
                # update row
                mob_sess = Model.session_map.objects.get(customer_info = payload["session_id"])
                mob_sess.service_type_id = payload["service_type_id"]
                mob_sess.save()

            else:
                pass
            return True
        
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    #check input validity
    def is_valid_from_redis(self,payload):
        try:
            # On HelloV only
            session_id = payload["session_id"]
            prev_question_id = payload["prev_question_id"]

            if prev_question_id == -1:
                return True
            if prev_question_id == -2:
                return True
            
            if app_settings.LOCAL_ENV == False and ((prev_question_id == 2 and payload["user_action"] == 4) or (prev_question_id == 50 and payload["user_action"] == -8)):                
                if payload['mobile_no'] in ['+919205264013','+919811374026','+917532973604','+919928927887']:
                    return True
                return False
            # if app_settings.LOCAL_ENV == False and ((prev_question_id == 2 and payload["user_action"] == 2) or (prev_question_id == 50 and payload["user_action"] == 2)):
            #     if payload['mobile_no'] in ['+919205264013']:
            #         return True
            #     return 'EMP service is down'
            # data from payload
            user_action = payload["user_action"]
            service_type_id = payload["service_type_id"]
            customer_type = int(payload['customer_type'])

            # Cache Implementation
            key = "valid_id_" + str(service_type_id) +"_"+ str(prev_question_id) +"_"+ str(user_action)
            cached_data = cache.get(key)

            if cached_data:
                return True

            if (customer_type == 1 or prev_question_id == 1) and prev_question_id != 50 and prev_question_id != -2: # myself
                com_model = Model.communication_myself.objects.filter(prev_question_id = prev_question_id, service_type_id = service_type_id, user_action = user_action).last()
        
            else: # someone else
                com_model = Model.communication_someoneelse.objects.filter(prev_question_id = prev_question_id, service_type_id = service_type_id, user_action = user_action).last()
            
        
            if com_model == None:
                # set cache key value
                cache.set(key, False, None)
                return False

            # set cache key value
            cache.set(key, True, None)
            return True

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
            