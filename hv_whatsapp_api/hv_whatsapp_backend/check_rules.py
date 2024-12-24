import json, re
import logging
import string
# import pytest
from datetime import date, datetime
from .address_extraction import AddressExtractor
from fuzzywuzzy import fuzz
# import textdistance as td
import numpy as np
from hv_whatsapp_api import models as Model
import logging
import inspect
import traceback

logging.basicConfig(filename="error_log.log")

class BaseRules():
    '''
    compare the name of customer for uan
    '''
    def compare_uan_name(self, val1, val2):
        try:
            THRESHOLD = 80
            return fuzz.token_sort_ratio(val1.lower(), val2.lower()) > THRESHOLD
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, val1, val2, fuzz_val):
        try:
            return fuzz.token_sort_ratio(val1.lower(), val2.lower()) > fuzz_val
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    check equality of two values
    '''
    def check_equal(self, val1, val2):
        try:
            return val1 == val2
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    check non-equality of two values
    '''
    def check_not_equal(self, val1, val2):
        try:
            return val1 != val2
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    check two strings match
    '''
    def str_equal(self, val1, val2):
        try:
            return val1.strip() == val2.strip()
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    check two strings match ignoring case
    '''
    def str_equal_ignore_case(self, val1, val2):
        try:
            return val1.strip().upper() == val2.strip().upper()
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    check two company matches
    '''
    def match_company_name(self, claimed_company_name, verified_company_arr):
        try:
            THRESHOLD = 75
            ### 1. if most recent company is the claimed company_name then its a green
            ### 2. if claimed company is not the verified_company_arr, then its a red
            ### 3. Any other scenario its a orange
            if fuzz.token_sort_ratio(claimed_company_name.lower(), verified_company_arr[0]['establishmentName'].lower()) > THRESHOLD:
                return Model.ps_color_code.green
                # return "GREEN"
            
            for arr in verified_company_arr:
                if fuzz.token_sort_ratio(claimed_company_name.lower(), arr['establishmentName'].lower()) > THRESHOLD:
                    return Model.ps_color_code.orange
                    # return "ORANGE"
            
            return Model.ps_color_code.red
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    check two strings match ignoring punctuations and whitespace
    '''
    def str_equal_ignore_ws_punct_case(self, val1, val2):
        try:
            remove = string.punctuation + string.whitespace
            v1 = val1.translate(val1.maketrans('', '', remove)).upper()
            v2 = val2.translate(val2.maketrans('', '', remove)).upper()
            # print(f'Comparing {v1} and {v2}')
            return v1 == v2
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    check dl not expire in 3 months
    '''
    def input_not_expiring_in3months(self, name, validity):
        try:
            if validity == "":
                return False
            elif len(validity.split("to"))==1 and (date(int(validity.split("-")[2]),int(validity.split("-")[1]),int(validity.split("-")[0]))-date.today()).days > 90:
                return True
            elif (date(int(validity.split("to")[1].strip().split("-")[2]),int(validity.split("to")[1].strip().split("-")[1]), int(validity.split("to")[1].strip().split("-")[0])) - date.today()).days  > 90:
                return True
            return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    check dl expiry in more than 3 months
    '''
    def greater_than3months_old(self, name, validity):
        try:
            if validity=="":
                return False
            if len(validity.split("to"))<2:
                return False
            if (date.today()-date(int(validity.split("to")[0].strip().split("-")[2]),int(validity.split("to")[0].strip().split("-")[1]), int(validity.split("to")[0].strip().split("-")[0]))).days > 90:
                return True
            return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    check dl expiry in more than 1 year
    '''
    def greater_than1year_old(self, name, validity):
        try:
            if validity=="":
                return False
            if len(validity.split("to"))<2:
                return False
            if (date.today()-date(int(validity.split("to")[0].strip().split("-")[2]),int(validity.split("to")[0].strip().split("-")[1]), int(validity.split("to")[0].strip().split("-")[0]))).days > 365:
                return True
            return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    cehck for lmv details in DL
    '''
    def contain_lmv_details(self,name,cov_details):
        try:
            if 'lmv' in str(cov_details).lower():
                return True
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
    def email_confirmation_validation(self, email_confirmation_response):
        try:
            if email_confirmation_response.lower() == "valid":
                return True
            return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
        
    '''
    candidate name match logic
    '''
    def candidate_name_match(self, individual_match):
        try:
            if individual_match[0]["match"] == True:
                return True
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
    def data_mx_records_match(self, data):
        try:
            if data["mx_records"] == True:
                return True
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
    def data_smtp_check_match(self, data):
        try:
            if data["smtp_check"] == True:
                return True
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

class CrimeCheckRulesProcessor(BaseRules):
       
    _filtered_list = []
    _user_details = {}

    def __init__(self, record_list,postal_response):
        self._filtered_list = record_list
        self._user_details = postal_response
        self.sorted_result = {}
        
        self.FATHER_NAME_FUZZ_THRESHHOLD = 80
        self.NAME_FUZZ_THRESHHOLD = 80
        self.LENIENT_NAME_FUZZ_THRESHHOLD = 75 # we increse threshhold from 50 to 75
        self.FULL_ADDRESS_FUZZ_THRESHHOLD = 75 # we increse threshhold from 75 to 85
        self.LOCALITY_MATCH_THRESHHOLD = 80
        self.MANUAL_THRESHHOLD = 80 # we increse threshhold from 80 to 90
        self.RED_THRESHHOLD = 110
        
        self.STATE_SCORE = 10
        self.DISTRICT_SCORE = 20
        self.PIN_SCORE = 30
        self.FATHER_NAME_SCORE = 30
        self.AGE_SCORE = 30
        self.HNO_SCORE = 30
        self.ADDRESS_PART_SCORE = 40
        
        self.STOP_WORDS = ['near', 'back', 'front', 'floor', 'top', 'down', 'shop', 'temple', 'mandir', 'behind', 'close', \
             'house', 'apartment', 'under', 'below', 'between', 'beside', 'next', 'into', 'within', 'inside', 'outside', \
                'room', 'home', 'ward', 'gaon', 'tehsil', 'distt', 'district', 'dist', 'vill', 'village', 'thana', 'police', \
                    'station', 'street', 'main', 'road', 'town', 'paas', 'peeche', 'nagar', 'mohalla', 'cross', 'bazar', 'bazaar', \
                        'mandir', 'park', 'gali', 'sector', 'block', 'grama', 'post', 'flat', 'hno', 'number', 'opposite']


    '''
    filter state and district and add the score for petioner and respondant
    '''    
    def filter_state_district(self):
        try:
            selected_items = []
            user_details = self._user_details

            for item in self._filtered_list:
                item['pscore'] = {'partial_name':False, 'full_name': False,'vill_initial_match': False, 'full_match':False, 'age': 0, 'father_name': 0, \
                    'pin': 0, 'state': 0, 'district': 0, 'hno': 0, 'local_area': 0, 'Untagged': 0, 'street': 0, \
                        'building': 0, 'complex': 0, 'blk_sec': 0, 'floor': 0, 'extra': 0, 'final_score': 0, 'matched_address': False}
                item['rscore'] = {'partial_name': False, 'full_name': False, 'vill_initial_match': False, 'full_match':False, 'age': 0, 'father_name': 0, \
                    'pin': 0, 'state': 0, 'district': 0, 'hno': 0, 'local_area': 0, 'Untagged': 0, 'street': 0, \
                        'building': 0, 'complex': 0, 'blk_sec': 0, 'floor': 0, 'extra': 0, 'final_score': 0, 'matched_address': False}
                # if item['position'] in [0, 40, 43, 49]: #temp
                #     print('temp')
                #     pass
                if item['petitionerAddress'] or len(item['petitioner']) > 25:
                    if not item['petitionerAddress'] and len(item['petitioner']) > 25:
                        item['petitionerAddress'] = item['petitioner']
                    pet_address = item['petitionerAddress'] + ' '
                    pet_address = re.sub(r'[,.\/-]',' ',pet_address)
                    if str(self._user_details['pin']) and (str(self._user_details['pin']) in pet_address.lower()):
                        item['pscore']['pin'] = self.PIN_SCORE
                    else:
                        if user_details['state'] and (user_details['state'].lower() in item['state'].lower()):
                            item['pscore']['state'] = self.STATE_SCORE
                        elif user_details['state'] and (user_details['state'].lower() in pet_address.lower() or (user_details['state_code'] and user_details['state_code'].lower() in pet_address.lower())):
                            item['pscore']['state'] = self.STATE_SCORE
                        if user_details['district'] and (user_details['district'].lower() in item['district'].lower()):
                            item['pscore']['district'] = self.DISTRICT_SCORE
                        elif user_details['district'] and fuzz.partial_token_set_ratio(user_details['district'].lower(), pet_address.lower()) >= 80 or (user_details['district_code'] and user_details['district_code'].lower() in pet_address.lower()):
                            item['pscore']['district'] = self.DISTRICT_SCORE
                if item['respondentAddress'] or len(item['respondent']) > 25:
                    if not item['respondentAddress'] and len(item['respondent']) > 25:
                        item['respondentAddress'] = item['respondent']
                    res_address = item['respondentAddress']
                    res_address = re.sub(r'[,.\/-]',' ',res_address)
                    if str(self._user_details['pin']) and (str(self._user_details['pin']) in res_address.lower()):
                        item['rscore']['pin'] = self.PIN_SCORE
                    else:
                        if user_details['state'] and user_details['state'].lower() in item['state'].lower():
                            item['rscore']['state'] = self.STATE_SCORE
                        elif user_details['state'] and (user_details['state'].lower() in res_address.lower() or (user_details['state_code'] and user_details['state_code'].lower() in res_address.lower())):
                            item['rscore']['state'] = self.STATE_SCORE
                        if user_details['district'] and (user_details['district'].lower() in item['district'].lower()):
                            item['rscore']['district'] = self.DISTRICT_SCORE
                        elif user_details['district'] and (fuzz.partial_token_set_ratio(user_details['district'].lower(), res_address.lower()) >= 80) or (user_details['district_code'] and user_details['district_code'].lower() in res_address.lower()):
                            item['rscore']['district'] = self.DISTRICT_SCORE
                        elif user_details['Untagged'] and (user_details['Untagged'].lower() in item['district'].lower()):
                            item['rscore']['district'] = self.DISTRICT_SCORE
                        elif user_details['Untagged'] and (fuzz.partial_token_set_ratio(user_details['Untagged'].lower(), res_address.lower()) >= 80):
                            item['rscore']['district'] = self.DISTRICT_SCORE
                selected_items.append(item)
            return selected_items
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())


    '''
    filter state and district and add the score for petioner and respondant
    '''
    def check_exact_state_district(self, item, clean_address, check):
        try:
            flag = False
            user_details = self._user_details
            # if item['position'] in [0, 40, 43, 49]: #temp
            #     print('temp')
            #     pass
            if check == 'pscore':
                if str(self._user_details['pin']) and (str(self._user_details['pin']) in clean_address.lower()):
                    flag = True
                else:
                    if user_details['state'] and (user_details['state'].lower() in item['state'].lower()):
                        flag = True
                    elif user_details['state'] and (user_details['state'].lower() in clean_address.lower() or (user_details['state_code'] and user_details['state_code'].lower() in clean_address.lower())):
                        flag = True
                    elif user_details['district'] and (user_details['district'].lower() in item['district'].lower()):
                        flag = True
                    elif user_details['district'] and fuzz.partial_token_set_ratio(user_details['district'].lower(), clean_address.lower()) >= 80 or (user_details['district_code'] and user_details['district_code'].lower() in clean_address.lower()):
                        flag = True
            elif check == 'rscore':
                if str(self._user_details['pin']) and (str(self._user_details['pin']) in clean_address.lower()):
                    flag = True
                else:
                    if user_details['state'] and user_details['state'].lower() in item['state'].lower():
                        flag = True
                    elif user_details['state'] and (user_details['state'].lower() in clean_address.lower() or (user_details['state_code'] and user_details['state_code'].lower() in clean_address.lower())):
                        flag = True
                    elif user_details['district'] and (user_details['district'].lower() in item['district'].lower()):
                        flag = True
                    elif user_details['district'] and (fuzz.partial_token_set_ratio(user_details['district'].lower(), clean_address.lower()) >= 80) or (user_details['district_code'] and user_details['district_code'].lower() in clean_address.lower()):
                        flag = True
                    elif user_details['Untagged'] and (user_details['Untagged'].lower() in item['district'].lower()):
                        flag = True
                    elif user_details['Untagged'] and (fuzz.partial_token_set_ratio(user_details['Untagged'].lower(), clean_address[-24:].lower()) >= 80):
                        flag = True
            return flag
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    '''
    Remove C/O and S/O string from address so that we get a good score when this address is matched 
    with claimed address.
    
    Input: Address
    Output: Cleaned address
    '''
    def remove_careof_sonof_extra_characters_from_address(self, address):
        try:
            address = address.lower().replace("C/O".lower(), "").replace("S/O".lower(), "")
            return address
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    Remove all the comma and dot from address, this will cover the case when we will be searching
    name inside the address string. Like searching : "Charan K" inside address having name "Charan. K"
    Input: Address
    Output: Cleaned Address
    '''
    def remove_dot_comma_from_address(self, address):
        try:
            address = re.sub("[.,]","", address.lower())
            return address
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    Remove name from the address
    '''
    def remove_name_from_address(self, address, petitioner, respondent):
        try:
            if petitioner.lower() in address.lower():
                address = address.replace(petitioner, "")
            if respondent.lower() in address.lower():
                address = address.replace(respondent, "")
            possible_names = self._user_details['possible_names']
            possible_names = set([item for current in possible_names for item in current.split(' ')])
            for possible_name in possible_names:
                address = address.replace(possible_name.lower(), "")
            return address
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    match exact name of candidate
    '''
    def fuzzy_exact_name_match(self, name, address, petitioner, respondent, p_r_name):
        try:
            match, exact_match, count = False, False, 0
            address = address.lower()
            name = name.lower()
            
            #logic for full name match
            if fuzz.token_set_ratio(name, address) >= self.NAME_FUZZ_THRESHHOLD:
                exact_match = True
            elif fuzz.token_set_ratio(name, petitioner) >= self.NAME_FUZZ_THRESHHOLD and p_r_name == 'pname':
                exact_match = True
            elif fuzz.token_set_ratio(name, respondent) >= self.NAME_FUZZ_THRESHHOLD and p_r_name == 'rname':
                exact_match = True
            
            #logic for partial name match
            if fuzz.partial_token_set_ratio(name, address) >= self.NAME_FUZZ_THRESHHOLD:
                match = True            
            elif fuzz.partial_token_set_ratio(name, petitioner) >= self.NAME_FUZZ_THRESHHOLD and p_r_name == 'pname':
                match = True            
            elif fuzz.partial_token_set_ratio(name, respondent) >= self.NAME_FUZZ_THRESHHOLD and p_r_name == 'rname':
                match = True            
            else:
                name = name.split()
                for item in name:                
                    if fuzz.partial_ratio(item, address) >= self.NAME_FUZZ_THRESHHOLD:                    
                        count = count + 1
                        match = True
                    else:
                        if len(name) >= 3 and count >= 2:
                            match = True
                            break
                        else:
                            match = False
            return match, exact_match
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False


    '''
    function to clean address field provided by API as respone
    Input : address, petitioner name and respondent nane
    Output : cleaned address
    '''
    def clean_address_fields(self, address, petitioner, respondent, user_details, p_r_name):
        try:
            father_name = user_details['father_name']
            final_address = (address.replace('\xa0', '').strip()).lower()
            father_name = father_name.lower()            
            name = ' '.join(user_details['name'])
            fuzzy_name_match, exact_name_match = self.fuzzy_exact_name_match(name, final_address, petitioner, respondent, p_r_name)
            final_address = final_address.replace(father_name, '').strip()
            if "Address".lower() in final_address.lower():  
                final_address = re.split("[Aa]ddress", final_address.lower())[1]
                if "Advocate".lower() in final_address.lower():
                    final_address = re.split("[Aa]dvocate",final_address.lower())[0]
                    final_address = re.sub(r"^\W+", "", final_address.lower())
                    final_address = re.sub(r"[\W+]+$", "", final_address.lower())
            elif "Advocate".lower() in address.lower():
                final_address = re.split("[Aa]dvocate",final_address.lower())[0]
                final_address = re.sub(r"^\W+", "", final_address.lower())
                final_address = re.sub(r"[\W+]+$", "", final_address.lower())
            
            final_address = self.remove_name_from_address(final_address, petitioner, respondent)
            final_address = self.remove_careof_sonof_extra_characters_from_address(final_address)
            final_address = self.remove_dot_comma_from_address(final_address)
            final_address = re.sub(' +', ' ', final_address)
            return final_address.strip(), fuzzy_name_match, exact_name_match
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
        
    def name_combination(self):
        from itertools import permutations, combinations
        namecombination = self._user_details['name']
        names = []
        for length in [2, 3]:
            for combo in combinations(namecombination, length):
                # For each combination, generate all possible orderings (permutations)
                for perm in permutations(combo):
                    names.append(" ".join(perm))
        self._user_details['name'] = names
        return True    
            

    '''
    get the exact name filter and ad rname, pname is name found in 
    repospondant and petitioner respectively
    '''
    def apply_name_filter(self):
        try:
            selected_list = []
            self.name_combination()
            for item in self._filtered_list:
                item['pname'] = False
                item['rname'] = False
                
                for possible_name in self._user_details['name']: #lowered matched score to avoid red miss
                    # if fuzz.partial_token_set_ratio(possible_name.lower(), item['petitioner'].lower()) >= self.LENIENT_NAME_FUZZ_THRESHHOLD or \
                    #     fuzz.partial_token_set_ratio(possible_name.lower(), item['petitionerAddress'].lower()) >= self.LENIENT_NAME_FUZZ_THRESHHOLD:
                    #     item['pname'] = True
                    # if fuzz.partial_token_set_ratio(possible_name.lower(), item['respondent'].lower()) >= self.LENIENT_NAME_FUZZ_THRESHHOLD or \
                    #     fuzz.partial_token_set_ratio(possible_name.lower(), item['respondentAddress'].lower()) >= self.LENIENT_NAME_FUZZ_THRESHHOLD:
                    #     item['rname'] = True
                    if fuzz.partial_ratio(possible_name.lower(), item['petitioner'].lower()) >= self.LENIENT_NAME_FUZZ_THRESHHOLD or \
                        fuzz.partial_ratio(possible_name.lower(), item['petitionerAddress'].lower()) >= self.LENIENT_NAME_FUZZ_THRESHHOLD:
                        item['pname'] = True
                    if fuzz.partial_ratio(possible_name.lower(), item['respondent'].lower()) >= self.LENIENT_NAME_FUZZ_THRESHHOLD or \
                        fuzz.partial_ratio(possible_name.lower(), item['respondentAddress'].lower()) >= self.LENIENT_NAME_FUZZ_THRESHHOLD:
                        item['rname'] = True
                if item['pname'] or item['rname']:
                    selected_list.append(item)

            return selected_list
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    add score if father name matches 
    '''
    def score_father_name(self):
        try:
            selected_list = []
            father_name = (self._user_details['father_name'].lower().strip()).split(' ')
            for item in self._filtered_list:
                for partial_father_name in father_name:
                    if item['petitionerAddress'] and (fuzz.partial_ratio(partial_father_name, item['petitionerAddress'].lower()) < self.FATHER_NAME_FUZZ_THRESHHOLD):
                        break
                else:
                    item['pscore']['father_name'] = self.FATHER_NAME_SCORE
                for partial_father_name in father_name:
                    if item["respondentAddress"] and (fuzz.partial_ratio(partial_father_name, item['respondentAddress'].lower()) < self.FATHER_NAME_FUZZ_THRESHHOLD):
                        break
                else:
                    item['rscore']['father_name'] = self.FATHER_NAME_SCORE
                selected_list.append(item)
            return selected_list
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    '''
    return True/False if addres match with locality, clean address within a threshold
    '''
    def match_address(self, locality, clean_address):
        try:
            count = 0
            local_area = locality.replace(","," ").strip()

            local_area = local_area.split(" ")
            local_area = [item for item in local_area if len(item) > 3 and item not in self.STOP_WORDS]
            local_len = len(local_area)
            if local_area:
                for l_area in local_area:
                    if fuzz.partial_ratio(' '+l_area.lower()+' ', clean_address.lower()) >= self.LOCALITY_MATCH_THRESHHOLD:
                        count = count + 1
                if fuzz.partial_ratio(' '+local_area[0].lower(), clean_address.lower()) >= self.LOCALITY_MATCH_THRESHHOLD:
                    return True
                if count == 0:
                    return False
                elif count >= local_len - 1 or count >= 3:
                    return True
            else:
                return False
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    return update score if addres match with locality and other details
    '''
    def match_locality(self, item, user_details, clean_address, type):
        try:
            
            if user_details['local_area'] and len(user_details['local_area']) > 2:
                if self.match_address(user_details['local_area'], clean_address):
                    item[type]['local_area'] = self.ADDRESS_PART_SCORE
                else:#it should at least match father name if locality exist but not matched
                    if 'near' in user_details['local_area'].lower():
                        pass
                    else:
                        item[type]['local_area'] = -10     
            if user_details['Untagged'] and len(user_details['Untagged']) > 2:
                if self.match_address(user_details['Untagged'], clean_address):
                    item[type]['Untagged'] = self.ADDRESS_PART_SCORE
                else:
                    if 'near' in user_details['Untagged'].lower():
                        pass
                    else:
                        item[type]['Untagged'] = -10
                        # pass
            if user_details['street'] and len(user_details['street']) > 2:
                if self.match_address(user_details['street'], clean_address):
                    item[type]['street'] = self.ADDRESS_PART_SCORE
                else:
                    if 'near' in user_details['street'].lower():
                        pass
                    else:
                        item[type]['street'] = -10  
            if user_details['building'] and len(user_details['building']) > 2:
                if self.match_address(user_details['building'], clean_address):
                    item[type]['building'] = self.ADDRESS_PART_SCORE
                else:
                    if 'near' in user_details['building'].lower():
                        pass
                    else:
                        item[type]['building'] = -10  
            if user_details['complex'] and len(user_details['complex']) > 2:
                if self.match_address(user_details['complex'], clean_address):
                    item[type]['complex'] =  self.ADDRESS_PART_SCORE
                else:
                    if 'near' in user_details['complex'].lower():
                        pass
                    else:
                        item[type]['complex'] = -10  
            if user_details['floor'] and len(user_details['floor']) > 2:
                if self.match_address(user_details['floor'], clean_address):
                    item[type]['floor'] =  self.ADDRESS_PART_SCORE
                else:
                    if 'near' in user_details['floor'].lower():
                        pass
                    else:
                        item[type]['floor'] = -10  
            if user_details['blk_sec'] and len(user_details['blk_sec']) > 2:
                match = re.search(r'(sector|block|sec|blk)[ ,./\-]*[0-9]{1,3}', user_details['blk_sec'].lower())
                addr_match = re.search(r'(sector|block|sec|blk)[ ,./\-]*[0-9]{1,3}', clean_address.lower())
                if match and addr_match:
                    add1 = re.sub('[ ]+', '', match.group())
                    add1 = re.sub('[,./\-]', '', add1)
                    # addr_match = re.search(r'(sector|block|sec|blk)[ ,./\-]*[0-9]{1,3}', clean_address.lower())
                    add2 = re.sub('[ ]+', '', addr_match.group())
                    add2 = re.sub('[,./\-]', '', add2)
                    num1 = re.search(r'[0-9]{1,3}', add1)
                    num2 = re.search(r'[0-9]{1,3}', add2)
                    if num1 and num2:
                        if num1.group() == num2.group():
                            item[type]['blk_sec'] =  self.ADDRESS_PART_SCORE
                    else:
                        if 'near' in user_details['blk_sec'].lower():
                            pass
                        else:
                            item[type]['blk_sec'] = -10
            if user_details['extra'] and len(user_details['extra']) > 2:
                if self.match_address(user_details['extra'], clean_address):
                    item[type]['extra'] =  self.ADDRESS_PART_SCORE//2
                else:
                    if 'near' in user_details['extra'].lower():
                        pass
            # final_score = local_area + untagged + street + building + complex1 + floor + blk_sec + extra
            return #final_score
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            

    '''
    calculate age from the address if available
    '''
    def get_age_from_address(self, address,filing_year, real_age):
        try:
            match = re.search(r'([0-9]{1,2}[ -]?ye?a?rs)|[0-9]{1,2}[ -]?age[d]?',address.lower())
            if match:
                x = match.group()
                match1 = re.search(r'[0-9]{1,2}',x)
                if match1:
                    y = match1.group()
                    age = int(y)
                    from datetime import datetime
                    year_diff = datetime.now().year - int(filing_year)
                    age = age + year_diff
                    if abs(real_age - age) < 3:
                        return self.AGE_SCORE
            return 0
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            

    def complete_address_match(self, claimed_clean_address, clean_address):
        try:
            vill_initial_match, full_match = False, False
            user_details = self._user_details
                        
            clean_address = clean_address.replace(user_details['state'], '')
            clean_address = clean_address.replace(user_details['district'], '')
            clean_address = clean_address.replace(user_details['district_code'], '')
            clean_address = clean_address.replace(str(user_details['pin']), '')
            clean_address = re.sub(r'(vill[age., ]{0,6})|(talu[ka., ]{0,5})|(tehsil[s., ]{0,5})|(at-)|(dist[rict., ]{0,9})', '', clean_address)
            clean_address = re.sub(r'[,.\/|-]','',clean_address).strip()           

            init_clean_address = clean_address.split(" ")
            init_clean_address = [item for item in init_clean_address if len(item) > 3 and item not in self.STOP_WORDS]
            init_clean_address = ' '.join(init_clean_address)
            
            init_match = re.search(r'([a-z]{4, 15})', claimed_clean_address)
            if not user_details['house'] and init_match:                
                init_str = init_match.group()
                if fuzz.partial_ratio(init_str, init_clean_address) >= self.FULL_ADDRESS_FUZZ_THRESHHOLD:
                    vill_initial_match = True
            full_match = fuzz.token_set_ratio(claimed_clean_address, init_clean_address) >= self.FULL_ADDRESS_FUZZ_THRESHHOLD
            return vill_initial_match, full_match
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    '''
    apply exact filter on petitioner and respondant address for certain conditions like
    bail applications, locality match, full address match, etc and update the score
    if score more than 80 then send all the cases list for manual verification
    '''
    def apply_exact_filter(self, final_result):
        try:
            selected_list = []
            max_score, prob_status = 0, 'NA'
            user_details = self._user_details
            user_details['local_area'] = re.sub(r'[,.\/|-]','',user_details['local_area'])
            user_details['Untagged'] = re.sub(r'[,.\/|-]','',user_details['Untagged'])
            user_details['street'] = re.sub(r'[,.\/|-]','',user_details['street'])
            user_details['building'] = re.sub(r'[,.\/|-]','',user_details['building'])
            user_details['complex'] = re.sub(r'[,.\/|-]','',user_details['complex']) 
            user_details['blk_sec'] = re.sub(r'[,.\/|-]','',user_details['blk_sec']) 
            user_details['floor'] = re.sub(r'[,.\/|-]','',user_details['floor']) 
            user_details['extra'] = re.sub(r'[,.\/|-]','',user_details['extra'])
            
            claimed_clean_address = user_details['address'].lower()
            claimed_clean_address = claimed_clean_address.replace(user_details['state'], '')
            claimed_clean_address = claimed_clean_address.replace(user_details['district'], '')
            claimed_clean_address = claimed_clean_address.replace(user_details['district_code'], '')
            claimed_clean_address = claimed_clean_address.replace(str(user_details['pin']), '')
            possible_names = self._user_details['possible_names']
            possible_names = list(set([item for current in possible_names for item in current.split(' ')]))
            for possible_name in possible_names:
                claimed_clean_address = claimed_clean_address.replace(possible_name.lower(), "")
            claimed_clean_address = re.sub(r'(vill[age., ]{0,6})|(talu[ka., ]{0,5})|(at-)|(tehsil[s., ]{0,10})', '', claimed_clean_address)                        
            claimed_clean_address = re.sub(r'[,.\/|-]','',claimed_clean_address)
            claimed_clean_address = re.sub(' +', ' ', claimed_clean_address).strip() 
            claimed_clean_address = claimed_clean_address.split(" ")
            claimed_clean_address = [item for item in claimed_clean_address if len(item) > 3 and item not in self.STOP_WORDS]
            claimed_clean_address = ' '.join(claimed_clean_address)
            

            for item in final_result:
                #for the bail application
                # if item["filingNumber"] in ["103157/2014"]: #temp
                #     print('temp')
                #     pass
                # if ('bail' in item['caseTypeName'].lower() or 'BA' in item['caseTypeName']) or ('bail' in item['caseType'].lower() or 'BA' in item['caseType']) and item['pname']:     
                if item['petitionerAddress'] or ('bail' in item['caseTypeName'].lower() or 'BA' in item['caseTypeName']) or ('bail' in item['caseType'].lower() or 'BA' in item['caseType']):
                    pet_address = item['petitionerAddress']
                    pet_address = re.sub(r'[\/-]',' ',pet_address)
                    pet_address = re.split(r'[0-9]+[).][^,a-zA-Z]', pet_address)
                    pet_address = [item for item in pet_address if item]
                    for address in pet_address:
                        old_score = item['pscore'].copy()
                        clean_address, name_match, exact_name_match = self.clean_address_fields(address, item['petitioner'], item['respondent'], user_details, 'pname')
                        item['pscore']['partial_name'], item['pscore']['full_name'] = name_match, exact_name_match
                        if len(clean_address) < 4: #very small address
                            continue
                        elif len(clean_address) < 20:
                            pass
                        else:
                            if self._user_details['house']: # if house number found in input address
                                len_add = len(clean_address)
                                hno = self._user_details['house']
                                part_address = re.sub(r'[ :,./-]{0,6}','',clean_address[0:(len_add-10)])
                                part_address = re.sub(r'number','',part_address)
                                match = re.search(r'^[@a-z]{0,25}[0-9]{1,8}', part_address)
                                if match: # if house number found in output address
                                    match = match.group()
                                    match = re.search(r'[0-9]{1,8}', match)
                                    match = int(match.group())
                                    if (hno.isnumeric() and abs(int(hno) - match) < 2) or \
                                        ' '+hno in clean_address[0:(len_add//2)] or \
                                            hno+' ' in clean_address[0:(len_add//2)]:
                                        item['pscore']['hno'] = self.HNO_SCORE
                        self.match_locality(item, user_details, clean_address, 'pscore')
                        item['pscore']['age'] = self.get_age_from_address(clean_address,item['year'], user_details['age'])
                        vill_initial_match, full_match = self.complete_address_match(claimed_clean_address, clean_address)
                        item['pscore']['vill_initial_match'], item['pscore']['full_match'] = vill_initial_match, full_match
                        # if item['pscore'] >= self.RED_THRESHHOLD and exact_name_match and is_full_match:
                        #     prob_status = 'Red'
                        #     selected_list.append(item)
                        #     break
                        item['pscore']['final_score'] = sum([item for item in list(item['pscore'].values()) if item != 0 and item != 1])
                        
                        if (item['pscore']['final_score'] >= self.MANUAL_THRESHHOLD and (name_match or exact_name_match)) and \
                            self.check_exact_state_district(item, clean_address, 'pscore') or \
                            (name_match and (vill_initial_match or full_match)):
                            item['pscore']['matched_address'] = address
                            selected_list.append(item)
                            break
                        else:
                            item['pscore'] = old_score
                if item['respondentAddress'] or item['rname']:
                    res_address = item['respondentAddress']
                    res_address = re.sub(r'[\/-]',' ',res_address)
                    res_address = re.split(r'[0-9]+[).][^,a-zA-Z]', res_address)
                    res_address = [item for item in res_address if item]
                    for address in res_address:
                        old_score = item['rscore'].copy()
                        clean_address, name_match, exact_name_match = self.clean_address_fields(address, item['petitioner'], item['respondent'], user_details, 'rname')
                        item['rscore']['partial_name'], item['rscore']['full_name'] = name_match, exact_name_match
                        if len(clean_address) < 4: #skip if very small address
                            continue
                        elif len(clean_address) < 20:
                            pass
                        else:
                            if self._user_details['house']: # if house number found in input address
                                len_add = len(clean_address)
                                hno = self._user_details['house']
                                part_address = re.sub(r'[ ,./-]{0,6}','',clean_address[0:(len_add-10)])
                                part_address = re.sub(r'number','',part_address)
                                match = re.search(r'^[@a-z]{0,25}[0-9]{1,8}', part_address)
                                if match: # if house number found in output address
                                    match = match.group()
                                    match = re.search(r'[0-9]{1,8}',match)
                                    match = int(match.group())
                                    if (hno.isnumeric() and abs(int(hno) - match) < 2)or \
                                        ' '+hno in clean_address[0:(len_add//2)] or \
                                            hno+' ' in clean_address[0:(len_add//2)]:
                                        item['rscore']['hno'] = self.HNO_SCORE
                        self.match_locality(item, user_details, clean_address, 'rscore')
                        item['rscore']['age'] = self.get_age_from_address(clean_address,item['year'], user_details['age'])
                        vill_initial_match, full_match = self.complete_address_match(claimed_clean_address, clean_address)
                        item['rscore']['vill_initial_match'], item['rscore']['full_match'] = vill_initial_match, full_match
                        # if item['rscore'] >= self.RED_THRESHHOLD and exact_name_match and is_full_match:
                        #     prob_status = 'Red'
                        #     selected_list.append(item)
                        #     break
                        item['rscore']['final_score'] = sum([item for item in list(item['rscore'].values()) if item != 0 and item != 1])
                        
                        if (item['rscore']['final_score'] >= self.MANUAL_THRESHHOLD and (name_match or exact_name_match)) and \
                            self.check_exact_state_district(item, clean_address, 'rscore') or \
                            (name_match and (vill_initial_match or full_match)):
                            item['rscore']['matched_address'] = address
                            selected_list.append(item)
                            break
                        else:
                            item['rscore'] = old_score
            return selected_list, prob_status
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            
    '''
    call all the functions step by step to get filtered result
    '''
    def process(self):
        try:
            self._filtered_list = self.filter_state_district()
            self._filtered_list = self.apply_name_filter()
            self._filtered_list = self.score_father_name()
        
            final_result, prob_status = self.apply_exact_filter(self._filtered_list)

            return final_result, self._user_details, prob_status
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False


'''
rule to match the name and fathername in DL
'''
class DrivingRules(BaseRules):
    def process(self, claimed, varified):
        try:
            claimed_ex = {}
            claimed_ex["applicant_name"] = claimed.name
            claimed_ex["father_name"] = claimed.father_name
            claimed_ex["dob"] = (claimed.dob).strftime("%d-%m-%Y")
            
            # print('DrivingRules-->', claimed_ex, varified)
            rules = [
                {
                    'rule_id': 'MATCH_NAMES',
                    'attr_id_1': 'applicant_name',
                    'attr_id_2': 'name',
                    'rule': 'str_equal_ignore_ws_punct_case'
                },
                {
                    'rule_id': 'MATCH FATHER NAME',
                    'attr_id_1': 'father_name',
                    'attr_id_2': 'father_name',
                    'rule': 'str_equal_ignore_ws_punct_case'
                },
                {
                    'rule_id': 'MATCH DOB',
                    'attr_id_1': 'dob',
                    'attr_id_2': 'dob',
                    'rule': 'str_equal_ignore_ws_punct_case'
                },
            ]
            for rule in rules:
                rule_name = rule['rule']
                method = getattr(self, rule_name)
                val1 = claimed_ex[rule['attr_id_1']]
                val2 = varified[rule['attr_id_2']]
                rule['result'] = method(val1, val2)
                
            # override name and father name matching
            rules[0]['result'] = self.compare_fuzz(claimed_ex[rules[0]['attr_id_1']], varified[rules[0]['attr_id_2']], 80)
            rules[1]['result'] = self.compare_fuzz(claimed_ex[rules[1]['attr_id_1']], varified[rules[1]['attr_id_2']], 80)
            rules[2]['result'] = self.compare_fuzz(claimed_ex[rules[2]['attr_id_1']], varified[rules[2]['attr_id_2']], 99)
            
            return json.dumps(rules)
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

'''
rule to match the name in UAN details
'''
class DERules(BaseRules):
    def process(self, claimed, verified):
        try:
            claimed_ex = {}
            claimed_ex["applicant_name"] = claimed.name

            rules = [
                {
                    'rule_id': 'MATCH_NAMES',
                    'attr_id_1': 'applicant_name',
                    'attr_id_2': 'name',
                    'rule': 'compare_uan_name'
                }
            ]

            name_result = self.compare_uan_name(claimed_ex['applicant_name'], verified['name'])

            rules[0]['result'] = name_result
            
            return json.dumps(rules)

        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False


'''
call criminal check rule processor to start the criminal address processing
'''
class CrimeRules(BaseRules):
    def process(self,list_of_cases, postal_response):
        try:
            processor = CrimeCheckRulesProcessor(list_of_cases, postal_response)
            filtered_list = processor.process()
            return filtered_list
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
