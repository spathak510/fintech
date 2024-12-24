import re, logging, traceback, inspect, datetime, json, requests, xmltodict, os
from fuzzywuzzy import fuzz
from datetime import date
import hv_whatsapp.settings as app_settings

class DLProcessor():

    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, param, fuzz_val):
        name_match = fuzz.token_sort_ratio(claimed_data['name'].lower(), param['name'].lower()) > fuzz_val
        father_name_match = fuzz.token_sort_ratio(claimed_data['father_name'].lower(), param['father_name'].lower()) > fuzz_val

        result = {
            'name_match': name_match,
            'father_name_match': father_name_match,
            'dl_no_match': True,
            'dob_match': True
        }
        return result


    def verify_driving_license_details(self, claimed_data, source_api_response):
        api_data = json.loads(source_api_response)
        param = {}
        if api_data['statusCode'] == 101:            
            param['name'] = api_data['result']['name'].lower().replace('  ', ' ')
            param['father_name'] = api_data['result']['father/husband'].lower().replace('  ', ' ')                
            result = self.compare_fuzz(claimed_data, param, 90)
            
            if 'user' in claimed_data and claimed_data['user'] == "certifier":
                claimed_data['name'] = param['name']
                claimed_data['father_name'] = param['father_name']
                
            claimed_data['name_match'] = result['name_match']
            claimed_data['father_name_match'] = result['father_name_match']
            claimed_data['dob_match'] = result['dob_match']
            claimed_data['dl_no_match'] = result['dl_no_match']
            claimed_data['source_api_response'] = source_api_response
            return claimed_data
        else:
            raise Exception('Source API is down')

    
    def process(self, claimed_data):
        url = app_settings.EXTERNAL_API['KARZAAPI_DL_v3']
        karza_key = app_settings.EXTERNAL_API['KARZAAPI_KEY']
        karza_key_id = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
        
        headers = {karza_key_id: karza_key}
        payload = {
        "dlNo": claimed_data['dl_no'],
        "dob": claimed_data['dob'].strftime('%d-%m-%Y'),
        "consent": "Y"
        }
        res = requests.post(url, data=json.dumps(payload), headers=headers)
        return res.text

class PANProcessor():

    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, api_data, fuzz_val):
        name_match = fuzz.token_sort_ratio(claimed_data['name'].lower(), api_data['result']['name'].lower()) >= fuzz_val        
        # name_match = fuzz.token_set_ratio(claimed_data['name'].lower(), api_data['result']['ocr_string'].lower()) >= fuzz_val
        return name_match

    def process(self, claimed_data):
        api_url = app_settings.EXTERNAL_API['KARZAAPI_PAN']
        headers = {
            'Content-Type': 'application/json',
            'x-karza-key': app_settings.EXTERNAL_API['KARZAAPI_KEY']
        }
        payload = {
        "pan": claimed_data['pan_no'],
        "consent": "Y"
        }
        res = requests.post(api_url, data=json.dumps(payload), headers=headers)
        claimed_data['source_api_response'] = res.text
        return json.loads(res.text)

    
    def verify_pan_details(self, claimed_data, api_data):
        name_match = self.compare_fuzz(claimed_data, api_data, 80)
        claimed_data['name_match'] = name_match
        claimed_data['pan_no_match'] = True
        return claimed_data

class VoterIDProcessor():
    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, param, fuzz_val):
        name_match = fuzz.token_sort_ratio(claimed_data['name'].lower(), param['name'].lower()) > fuzz_val
        father_name_match = fuzz.token_sort_ratio(claimed_data['father_name'].lower(), param['father_name'].lower()) > fuzz_val
        dob_match = claimed_data['dob'].strftime('%d-%m-%Y') == param['dob']
        gender_match = claimed_data['gender'].lower() == param['gender']
        
        if 'user' in claimed_data and claimed_data['user'] == "certifier":
            claimed_data['name'] = param['name']
            claimed_data['father_name'] = param['father_name']
            claimed_data['dob'] = param['dob'].strftime('%Y-%m-%d') if param['dob'] else claimed_data['dob']
            claimed_data['gender'] = param['gender']
        
        claimed_data['name_match'] = name_match
        claimed_data['father_name_match'] = father_name_match
        claimed_data['dob_match'] = dob_match
        claimed_data['gender_match'] = gender_match
        return claimed_data

    def verify_voter_id_details(self, claimed_data, api_data):
        param = {}        
        param['name'] = api_data['result']['name'].lower().replace(' -', '')
        param['father_name'] = api_data['result']['rln_name'].lower().replace(' -', '')
        param['gender'] = 'male' if api_data['result']['gender'].lower() == 'm' else 'female'
        param['dob'] = api_data['result']['dob']
            
        return self.compare_fuzz(claimed_data, param, 90)

    
    def process(self, claimed_data):
        url = app_settings.EXTERNAL_API['KARZAAPI_VOTER']
        karza_key = app_settings.EXTERNAL_API['KARZAAPI_KEY']
        karza_key_id = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
        headers = {karza_key_id: karza_key}
        payload = {
        "epic_no": claimed_data['voter_id_no'],
        "consent": "Y"
        }
        res = requests.post(url, data=json.dumps(payload), headers=headers)
        claimed_data['source_api_response'] = res.text
        return json.loads(res.text)

class PassportProcessor():
    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, param, fuzz_val):
        name_match = fuzz.token_set_ratio(claimed_data['name'].lower(), param['name'].lower()) > fuzz_val
        passport_no_match = (claimed_data['passport_no'].lower() == param['passport_no'].lower())

        claimed_data['name_match'] = name_match
        claimed_data['passport_no_match'] = passport_no_match
        return claimed_data


    def verify_passport_details(self, claimed_data, api_data):
        param = {}
        param['name'] = api_data['result']['name']['nameFromPassport'] + ' ' + api_data['result']['name']['surnameFromPassport']
        param['passport_no'] = api_data['result']['passportNumber']['passportNumberFromSource']
        self.compare_fuzz(claimed_data, param, 90)
        return claimed_data


    def process(self, claimed_data):
        url = app_settings.EXTERNAL_API['KARZAAPI_PASSPORT']
        karza_key = app_settings.EXTERNAL_API['KARZAAPI_KEY']
        karza_key_id = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
        headers = {karza_key_id: karza_key}
        
        payload = {
        "consent": "y",
        "fileNo": claimed_data['file_no'],
        "dob": claimed_data['dob'].strftime('%d/%m/%Y'),
        }
        res = requests.post(url, data=json.dumps(payload), headers=headers)
        claimed_data['source_api_response'] = res.text
        return json.loads(res.text)

class AadhaarProcessor():

    def process(self, claimed_data):
        url = app_settings.EXTERNAL_API['AADHAAR_URL']
        payload = {
                "uid_no":claimed_data['aadhaar_no']
            }
        res = requests.post(url, data=payload, headers={})
        print(str(res.text))
        claimed_data['source_api_response'] = res.text
        result = json.loads(res.text)
        if result.get('status', '') == 'Fail':
            raise Exception("Sorry, Broken aadhaar api")
        return result

    '''
    validate the age from customer and api response
    '''
    def validate_age(self,age,age_range, yob):
        in_range = age_range.split('-')
        low_range = int(in_range[0])
        up_range = int(in_range[1])
        if low_range <= age <= up_range:
            return True
        if yob and (low_range-1 <= age <= up_range+1):
            return True
        return False

    
    def calculate_age(self, birthdate):
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age


    def verify_aadhaar_details(self, claimed_data, api_data):
        claimed_data['aadhaar_mobile_no'] = api_data['maskedMobileNumber']
        claimed_data['state_match'] = fuzz.token_set_ratio(claimed_data['address'].lower(), api_data['address'].lower()) >= 80
        claimed_data['gender_match'] = claimed_data['gender'].lower() == api_data['gender'].lower()
        
        age = self.calculate_age(claimed_data['dob'])
        yob = claimed_data.get('yob', False)
        claimed_data['age_match'] = self.validate_age(age, api_data['ageBand'], yob)
        claimed_data['age_range'] = api_data['ageBand']
        claimed_data['state'] = api_data['address']
        return claimed_data

class CriminalVerificationProcessor():

    def process(self, claimed_data):
        import secrets
        url = app_settings.EXTERNAL_API['CRIME_CHECK']
        key = app_settings.EXTERNAL_API['CRIME_CHECK_KEY']
        headers = {'Content-Type': 'application/json', 'Authorization': key}
        payload = {
        "order_id": claimed_data.get('order_id', secrets.token_hex(8)),
        "name": claimed_data['name'],
        "fatherName": claimed_data['father_name'],
        "address": claimed_data['address'],
        "dob": claimed_data['dob'].strftime('%d-%m-%Y'),
        "source_name": claimed_data.get('source_name', 'HVAPP'),
        "existing_record": False
        }
        
        res = requests.post(url, data=json.dumps(payload), headers=headers)
        res = json.loads(res.text)
        claimed_data['source_api_response'] = res["result"]["crime_api_result"]
        rule_engine_result = res["result"]["rule_engine_result"]
        
        if len(json.loads(rule_engine_result)) > 0:
            claimed_data['criminal_case_found'] = True
            claimed_data['rule_engine_result'] = rule_engine_result
        return True,res

class AadhaarOfflineProcessor():
    
    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, api_data, fuzz_val):
        name_match = fuzz.token_sort_ratio(claimed_data['name'].lower(), api_data['name'].lower()) == fuzz_val
        # father_name_match = fuzz.token_set_ratio(claimed_data['father_name'].lower(), api_data['careof'].lower()) == fuzz_val
        # dob = claimed_data['dob'] == api_data['dob']
        return name_match # and father_name_match and dob
            
    def fetch_data(self, data_dict):
        aadhaar_dic = {}
        aadhaar_dic['name'] = data_dict['OfflinePaperlessKyc']['UidData']['Poi']['@name']
        aadhaar_dic['dob'] = data_dict['OfflinePaperlessKyc']['UidData']['Poi']['@dob']
        aadhaar_dic['gender'] = data_dict['OfflinePaperlessKyc']['UidData']['Poi']['@gender']
        aadhaar_dic['careof'] = data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@careof']            
        address = ''
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@house'] + ' '
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@street'] + ' '
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@loc'] + ' '
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@landmark'] + ' '
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@subdist'] + ' '
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@vtc'] + ' '
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@po'] + ' '
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@state'] + ' '
        address = address + data_dict['OfflinePaperlessKyc']['UidData']['Poa']['@pc'] + ' '
        aadhaar_dic['address'] = address.replace('  ', '')
        aadhaar_dic['pic'] = data_dict['OfflinePaperlessKyc']['UidData']['Pht']
        return aadhaar_dic


    def process(self, claimed_data):
        import base64
        encoded_zip = claimed_data['aadhar_zip_file']
        decoded_zip = base64.b64decode(encoded_zip)
        file_name = claimed_data['request_id'] + '.zip'
        with open(file_name, 'wb') as f:
            f.write(decoded_zip)
        import zipfile, glob

        pswd = claimed_data['aadhaar_pin_to_open_file']


        with zipfile.ZipFile(file_name) as file:
            # password you pass must be in the bytes you converted 'str' into 'bytes'
            file.extractall(pwd = bytes(pswd, 'utf-8'))

        f_name = glob.glob('offlineaadhaar*.xml')[0]
        with open(f_name) as xml_file:      
            data_dict = xmltodict.parse(xml_file.read())

        res = self.fetch_data(data_dict)
        os.remove(f_name)
        os.remove(file_name)
        return res

    
    def verify_aadhaar_details(self, claimed_data, api_data):
        is_name_match = self.compare_fuzz(claimed_data, api_data, 100)
        return is_name_match
