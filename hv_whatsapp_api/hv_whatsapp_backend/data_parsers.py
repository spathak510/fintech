import json
import html
import copy
# from xmljson import parker, Parker
# from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring

import logging
import inspect
from datetime import datetime
import traceback

logging.basicConfig(filename="error_log.log")

'''
NOT IN USE
'''
class CommonDataParser():
    pass

'''
{
  "result": {
    "ps_lat_long": "0.0,0.0",
    "rln_name_v1": "केदारनाथ गुप्ता",
    "rln_name_v2": "",
    "rln_name_v3": "",
    "part_no": "563",
    "rln_type": "F",
    "section_no": "1",
    "id": "S240550563010537",
    "epic_no": "XPD0573022",
    "rln_name": "Kedaranath Gupta",
    "district": "Ghaziabad",
    "last_update": "Tue Jun 18 15:37:24 IST 2019",
    "state": "Uttar Pradesh",
    "ac_no": "55",
    "house_no": "B-305",
    "ps_name": ",2 ",
    "pc_name": "Ghaziabad",
    "slno_inpart": "537",
    "name": "Ashutosh",
    "part_name": "DELHI PUBLIC SCHOOL AHINSHA KHAND 2 INDRAPURAM",
    "dob": "",
    "gender": "M",
    "age": 29,
    "ac_name": "Sahibabad",
    "name_v1": "आशुतोष",
    "st_code": "S24",
    "name_v3": "",
    "name_v2": ""
  },
  "request_id": "647dac1f-1b5a-4890-ba0c-e2aaf165eb9e",
  "status-code": "101"
}
'''

'''
NOT IN USE
'''
class VoterDataParser(CommonDataParser):
    def parse_data(self, json_str):
        try:
            if not json_str:
                return {}
            json_obj = json.loads(json_str)
            result_obj = {}
            result_obj['request_id'] = json_obj['request_id']
            result_obj['status_code'] = json_obj['status-code']
            
            # if result_obj['status_code'] == '101':
            #     result_obj['ps_lat_long'] = json_obj['result']['ps_lat_long']
            #     result_obj['rln_name_v1'] = json_obj['result']['rln_name_v1']
            #     result_obj['rln_name_v2'] = json_obj['result']['rln_name_v2']
            #     result_obj['rln_name_v3'] = json_obj['result']['rln_name_v3']
            #     result_obj['part_no'] = json_obj['result']['part_no']
            #     result_obj['rln_type'] = json_obj['result']['rln_type']
            #     result_obj['section_no'] = json_obj['result']['section_no']
            #     result_obj['id'] = json_obj['result']['id']
            #     result_obj['epic_no'] = json_obj['result']['epic_no']
            #     result_obj['rln_name'] = json_obj['result']['rln_name']
            #     result_obj["district"] = json_obj['result']['district']
            #     result_obj["last_update"] = json_obj['result']['last_update']
            #     result_obj["state"] = json_obj['result']['state']
            #     result_obj["ac_no"] = json_obj['result']['ac_no']
            #     result_obj["house_no"] = json_obj['result']['house_no']
            #     result_obj["ps_name"] = json_obj['result']['ps_name']
            #     result_obj["pc_name"] = json_obj['result']['pc_name']
            #     result_obj["slno_inpart"] = json_obj['result']['slno_inpart']
            #     result_obj["name"] = json_obj['result']['name']
            #     result_obj["part_name"] = json_obj['result']['part_name']
            #     result_obj["dob"] = json_obj['result']['dob']
            #     result_obj["gender"] = json_obj['result']['gender']
            #     result_obj["age"] = json_obj['result']['age']
            #     result_obj["ac_name"] = json_obj['result']['ac_name']
            #     result_obj["name_v1"] = json_obj['result']['name_v1']
            #     result_obj["st_code"] = json_obj['result']['st_code']
            #     result_obj["name_v3"] = json_obj['result']['name_v3']
            #     result_obj["name_v2"] = json_obj['result']['name_v2']
            # else:
            #     return result_obj
            
            return result_obj
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

'''
parse the DL response and create a json
'''        
class DrivingLicenseDataParser(CommonDataParser):
    def parse_data(self, json_str):
        try:

            if not json_str:
                return {}
            # str_txt = json_str.replace('b\'', '').replace('\'', '')
            json_obj = json.loads(json_str)
            result_obj = {}
            result_obj['request_id'] = json_obj['request_id']
            result_obj['status_code'] = json_obj['status-code']

            if result_obj['status_code'] == '101':
                result_obj['name'] = json_obj['result']['name']
                result_obj['father_name'] = json_obj['result']['father/husband']
                result_obj['issue_date'] = json_obj['result']['issue_date']
                result_obj['dob'] = json_obj['result']['dob']
                result_obj['blood_group'] = json_obj['result']['blood_group']
                result_obj['img'] = json_obj['result']['img']
                result_obj['nt_valid'] = json_obj['result']['validity']['non-transport']
                result_obj['t_valid'] = json_obj['result']['validity']['transport']
                result_obj['address'] = json_obj['result']['address']
                result_obj['cov'] = json_obj['result']['cov_details']
                result_obj['v_class'] = json_obj['result']['cov_details'][0]['cov'] ## class of vehicle
                result_obj['auth'] = json_obj['result']['cov_details'][0]['issue_date']
            else:
                return result_obj
            return result_obj

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

'''
NOT IN USE
'''
class AddressViaDLDataParser(CommonDataParser):
    def parse_data(self, json_str):
        try:
            if not json_str:
                return {}
            json_obj = json.loads(json_str)
            result_obj = {}
            result_obj['request_id'] = json_obj['request_id']
            result_obj['status_code'] = json_obj['status-code']

            if result_obj['status_code'] == '101':
                result_obj['name'] = json_obj['result']['name']
                result_obj['address'] = json_obj['result']['address']
                return result_obj
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

'''
NOT IN USE
'''
class LPGDataParser(CommonDataParser):
    def parse_data(self, json_str):
        try:
            if not json_str:
                return {}
            json_obj = json.loads(json_str)
            result_obj = {}
            result_obj['request_id'] = json_obj['request_id']
            result_obj['status_code'] = json_obj['status-code']

            if result_obj['status_code'] == '101':
                result_obj['name'] = json_obj['result']['ConsumerName']
                result_obj['address'] = json_obj['result']['ConsumerAddress']
                return result_obj
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

'''
NOT IN USE
'''
class UANOTPDataParser(CommonDataParser):
    def parse_data(self, json_str):
        try:
            if not json_str:
                return {}
            json_obj = json.loads(json_str)
            
            result_obj = {}
            result_obj['request_id'] = json_obj['request_id']
            result_obj['status_code'] = json_obj['status-code']

            return result_obj
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

'''
NOT IN USE
'''
class PANDataParser(CommonDataParser):
    def parse_data(self, json_str):
        try:
            if not json_str:
                return {}
            json_obj = json.loads(json_str)
            
            result_obj = {}
            result_obj['request_id'] = json_obj['request_id']
            result_obj['status_code'] = json_obj['status-code']

            return result_obj
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
'''
parse the UAN details
'''    
class DEDataParser(CommonDataParser):
    def get_company_arr(self, json_result):
        company_dict = json_result
        company_dict.sort(key=lambda x:x['doj'], reverse=True)
        return company_dict
            
    def get_candidate_name(self, json_obj):
        json = json_obj[0]
        return json['name']
    def parse_data(self, json_str):
        try:
            json_obj = json.loads(json_str)
            result_obj = {}
            result_obj['est_name'] = json_obj['payload']['passbook'][0]['est_name']
            result_obj['member_name'] = json_obj['payload']['passbook'][0]['member_name']
            result_obj['dob'] = json_obj['payload']['passbook'][0]['dob']
            result_obj['doj_epf'] = json_obj['payload']['passbook'][0]['doj_epf']
            result_obj['father_name'] = json_obj['payload']['passbook'][0]['father_name']
            result_obj['particular'] = json_obj['payload']['passbook'][-1]['particular']
            return result_obj
    
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

'''
NOT IN USE
'''
class UANDataParser(CommonDataParser):
    def parse_data(self, json_str):
        if not json_str:
            return {}
        # str_txt = json_str.replace('b\'', '').replace('\'', '')
        json_obj = json.loads(json_str)
        return json_obj.result.uan

'''
parse the criminal record details from api
'''
class CrimeDataParser(CommonDataParser):
    def parse_data(self, json_str):
        try:
            if not json_str:
                return {}
            # str_txt = json_str.replace('b\'', '').replace('\'', '')
            json_obj = json.loads(json_str)
            return {
                'details': json_obj['details'],
                'totalHits': json_obj['totalHits']
            }
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
