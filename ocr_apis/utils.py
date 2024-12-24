import re, logging, traceback, inspect, datetime, json, requests, xmltodict, os
from fuzzywuzzy import fuzz
import hv_whatsapp.settings as app_settings


class PanProcessor():

    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, api_data, fuzz_val):
        try:
            name_match = fuzz.token_sort_ratio(claimed_data['name'].lower(), api_data['result']['name'].lower()) == fuzz_val
            return name_match
            
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def process(self, claimed_data):
        try:
            api_url = app_settings.EXTERNAL_API['KARZAAPI_PAN']
            headers = {
                'Content-Type': 'application/json',
                'x-karza-key': app_settings.EXTERNAL_API['KARZAAPI_KEY']
            }
            payload = {
            "pan": claimed_data['pan_number'],
            # "name": claimed_data['name'],
            # "dob": claimed_data['dob'],
            "consent": "Y"
            }
            payload_str = json.dumps(payload)
            res = requests.post(api_url, data=payload_str, headers=headers)
            return res.text
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    def validate_pan(self, claimed_data, api_data):
        try:
            is_name_match = self.compare_fuzz(claimed_data, api_data, 100)
            
            return is_name_match
            
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

class AadhaarProcessor():
    
    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, api_data, fuzz_val):
        try:
            name_match = fuzz.token_sort_ratio(claimed_data['name'].lower(), api_data['name'].lower()) == fuzz_val
            # father_name_match = fuzz.token_set_ratio(claimed_data['father_name'].lower(), api_data['careof'].lower()) == fuzz_val
            # dob = claimed_data['dob'] == api_data['dob']
            return name_match # and father_name_match and dob
            
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def fetch_data(self, data_dict):
        try:
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
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def process(self, claimed_data):
        try:
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
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    def validate_aadhaar(self, claimed_data, api_data):
        try:
            is_name_match = self.compare_fuzz(claimed_data, api_data, 100)
            
            return is_name_match
            
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

class DLApiBackend():

    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, param, fuzz_val):
        try:
            name = fuzz.token_sort_ratio(claimed_data['name'].lower(), param['name'].lower()) > fuzz_val
            father_name = fuzz.token_sort_ratio(claimed_data['father_name'].lower(), param['father_name'].lower()) > fuzz_val

            return name and father_name
            
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def verify_driving_license(self, claimed_data, dl_obj):
        try:
            api_data = json.loads(dl_obj.api_response)
            param = {}
            if api_data['statusCode'] != 101:
                res = self.get_data_from_karza(claimed_data)
                dl_obj.api_response = res
                api_data = json.loads(res)
            
            param['name'] = api_data['result']['name'].lower().replace('  ', ' ')
            param['father_name'] = api_data['result']['father/husband'].lower().replace('  ', ' ')
                
            return self.compare_fuzz(claimed_data, param, 90)

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def match_and_replace_param(self, param, ocr_string, result, img):
        try:
            if img == 'front':
                if fuzz.token_set_ratio(param['name'], ocr_string) >= 90:
                    result['name'] = param['name']            
                if fuzz.token_set_ratio(param['father_name'], ocr_string) >= 80:
                    result['father_name'] = param['father_name']
                if fuzz.token_set_ratio(param['address'], ocr_string) >= 70:
                    result['address'] = param['address']
            else:
                if fuzz.token_set_ratio(param['father_name'], ocr_string) >= 80:
                    result['father_name'] = param['father_name']
                if fuzz.token_set_ratio(param['address'], ocr_string) >= 70:
                    result['address'] = param['address']
            return result
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    def get_data_from_karza(self, result):
        try:
            url = app_settings.EXTERNAL_API['KARZAAPI_DL_v3']
            karza_key = app_settings.EXTERNAL_API['KARZAAPI_KEY']
            karza_key_id = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
            headers = {karza_key_id: karza_key}
            payload = {
            "dlNo": result['dl_number'],
            "dob": result['dob'],
            "consent": "Y"
            }
            payload_str = json.dumps(payload)
            res = requests.post(url, data=payload_str, headers=headers)
            return res.text
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def get_dl_front_result(self, ocr_string):
        try:
            dl_list = {}
            dl_list['ocr_string'] = ocr_string
            input_str = ocr_string #request['string']
            input_str = input_str.lower().replace('\n', ' ')
            #DL number
            search_dl = r'([a-z0-9]{1,4}[-,/, ]?[0-9]{2}[-,/, ]?\d{4}[ ]?\d{4,9})|([a-z]{2}\d{2}[a-z]{1}[-,/, ]\d{4}[-,/, ]\d{7})|(\d{1,2}[/,-]?\d{3,5}[/,-]?\d{4})'
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
                    dl_list['dob'] = datemin.strftime("%d-%m-%Y")
                else:
                    months = {"jan":"01", "feb":"02", "mar":"03", "apr":"04", "may":"05", "jun":"06", "jul":"07", "aug":"08", "sep":"09", "oct":"10", "nov":"11", "dec":"12"}
                    dob_special_matches = []
                    dob_special = "\d{2}[- ]\w{3}[- ]\d{4}"
                    dobMatch = re.findall(dob_special, input_str)
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
                            dl_list['dob'] = datemin.strftime("%d-%m-%Y")
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
            add_str = 'add[ress.: ]{1,7}'
            match_addr = re.search(add_str, input_str)
            hno_str = r'([ ]h[. ]?no[. ]?)|(house[no. ]{3,5})|(room[no. ]{3,5})|(flat[ no.-]{3,5})'
            match_hno = re.search(hno_str, input_str)
            if match_hno:
                index_add = match_hno.start()
                len_addr = 0
            elif match_addr:
                len_addr = len(match_addr.group())
                index_add = match_addr.start()
            if match_pin:
                index_pin = match_pin.start()
            if match_pin and (match_addr or match_hno) and (index_pin - index_add) > 30:
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
            if 'delhi' in ocr_string or 'nct' in ocr_string or 'dl' in dl_list['dl_number']:
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
            return response

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


    # DL Back Image Processor
    def get_dl_back_result(self, ocr_string):
        try:
            dl_list = {}
            dl_list['ocr_string'] = ocr_string
            input_str = ocr_string #request['string']
            input_str = input_str.lower().replace('\n', ' ')
            #DL number
            search_dl = r'([a-z0-9]{1,3}[-,/, ]{0,1}[0-9]{2}[-,/, ]{0,1}\d{8,13})|([a-z]{2}\d{2}[a-z]{1}[-,/, ]\d{4}[-,/, ]\d{7})|(\d{2}[/,-]{0,1}\d{4}[/,-]{0,1}\d{4})'
            ls = re.search(search_dl, input_str)
            if ls: 
                dl_list['dl_number'] = ls.group()
            else:
                return False
                
            #address
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
                    dl_list['address'] = ''

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
            response = dl_list
            return response

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


class VoterIDProcessor():
    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, param, fuzz_val):
        try:
            name = fuzz.token_sort_ratio(claimed_data['name'].lower(), param['name'].lower()) > fuzz_val
            father_name = fuzz.token_sort_ratio(claimed_data['father_name'].lower(), param['father_name'].lower()) > fuzz_val
            # dob = (claimed_data['dob'] == param['dob'])

            return name and father_name
            
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def verify_voter_id(self, claimed_data, voter_obj):
        try:
            param = {}
            if voter_obj.api_response:
                api_data = json.loads(voter_obj.api_response)
                
                if api_data['status-code'] != '101':
                    res = self.get_data_from_karza(claimed_data)
                    voter_obj.api_response = res
                    api_data = json.loads(res)
            
            param['name'] = api_data['result']['name'].lower().replace(' -', '')
            param['father_name'] = api_data['result']['rln_name'].lower().replace(' -', '')
            # param['dob'] = api_data['result']['dob']
                
            return self.compare_fuzz(claimed_data, param, 90)

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def match_and_replace_param(self, param, ocr_string, result, img):
        try:
            if img == 'front':
                if fuzz.token_set_ratio(param['name'], ocr_string) >= 90:
                    result['name'] = param['name']            
                if fuzz.token_set_ratio(param['father_name'], ocr_string) >= 90:
                    result['father_name'] = param['father_name']
            # else:
            #     if fuzz.token_set_ratio(param['father_name'], ocr_string) >= 90:
            #         result['father_name'] = param['father_name']
            #     if fuzz.token_set_ratio(param['address'], ocr_string) >= 90:
            #         result['address'] = param['address']
            return result
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    def get_data_from_karza(self, result):
        try:
            url = app_settings.EXTERNAL_API['KARZAAPI_VOTER']
            karza_key = app_settings.EXTERNAL_API['KARZAAPI_KEY']
            karza_key_id = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
            headers = {karza_key_id: karza_key}
            payload = {
            "epic_no": result['vid'],
            "consent": "Y"
            }
            payload_str = json.dumps(payload)
            res = requests.post(url, data=payload_str, headers=headers)
            return res.text
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def get_voter_front_result(self, ocr_string):
        try:
            voter_list = {}
            voter_list['ocr_string'] = ocr_string
            input_str = ocr_string.lower()
            #voter id number working perfect
            search_no = r'[a-z]{3}[0-9]{7}'
            vid = re.search(search_no, input_str)
            if vid: 
                vid = vid.group()
                voter_list['vid'] = vid
            else:
                return False

            #gender search works perfect
            search_gender = r'male|female'
            gender = re.search(search_gender, input_str)
            if gender:
                gender = gender.group()
                voter_list['gender'] = gender

            #dob working perfect
            if 'birth' in input_str or 'dob' in input_str:
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
                    voter_list['dob'] = datemin.strftime("%d-%m-%Y")

            #name match working perfect
            name_ind = input_str.find('name')
            name_str = input_str[name_ind+4:]
            search_name = r'(\n)?[: ]{0,3}[a-z]+[ ]?[a-z]*[ ]?[a-z]*\n'
            name = re.search(search_name, name_str)
            if name:
                name = name.group().replace(':','').replace('\n','').strip()
                voter_list['name'] = name

            #father's name working almost perfect
            name_ind = input_str.rfind('name')
            fname_str = input_str[name_ind+4:]
            search_name = r'(\n)?[: ]{0,3}[a-z]+[ ]?[a-z]*[ ]?[a-z]*\n'
            name = re.search(search_name, fname_str)
            if name:
                name = name.group().replace(':','').replace('\n','').replace('sex','').strip()
                voter_list['father_name'] = name
            else:
                father_ind = input_str.rfind('father')
                fname_str = input_str[father_ind+8:]
                search_name = r'(\n)?[: ]{0,3}[a-z]+[ ]?[a-z]*[ ]?[a-z]*\n'
                name = re.search(search_name, fname_str)
                if name:
                    name = name.group().replace(':','').replace('\n','').replace('name','').replace('sex','').strip()
                    voter_list['father_name'] = name
            return voter_list
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
    
    def get_voter_back_result(self, ocr_string):
        try:
            voter_list = {}
            voter_list['ocr_string'] = ocr_string
            input_str = ocr_string.lower().replace('\n',' ')

            #voter id number working perfect
            search_no = r'[a-z]{3}[0-9]{7}'
            vid = re.search(search_no, input_str)
            if vid: 
                vid = vid.group()
                voter_list['vid'] = vid

            #gender search works perfect
            search_gender = r'male|female'
            gender = re.search(search_gender, input_str)
            if gender:
                gender = gender.group()
                voter_list['gender'] = gender

            #dob working perfect
            if 'birth' in input_str or 'dob' in input_str:
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
                    voter_list['dob'] = datemin.strftime("%d-%m-%Y")

            #address working perfect
            add_ind = input_str.find('addres')
            address_str = input_str[add_ind:]
            pin_str = r'[ :-][1-9][0-9]{5}[ .:-]'
            match_pin = re.search(pin_str, address_str)
            if match_pin:
                pin_index = address_str.find(match_pin.group()) + 7
            if not match_pin or (match_pin and (pin_index > address_str.find('date'))):
                address_str = address_str[0:address_str.find('date')]
            else:
                address_str = address_str[0:pin_index]
            voter_list['address'] = address_str.encode("ascii", "ignore").decode("utf-8").replace('address','').replace(':','').strip()
            return voter_list
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

class PassportIDProcessor():
    '''
    compare two values and return True/False if condition satisfies
    '''
    def compare_fuzz(self, claimed_data, param, fuzz_val):
        try:
            name = fuzz.token_set_ratio(claimed_data['name'].lower(), param['name'].lower()) > fuzz_val
            # pno = (claimed_data['passport_no'].lower() == param['passport_no'].lower())
            return name
            
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def verify_passport_id(self, claimed_data, passport_obj):
        try:
            param = {}
            res = self.get_data_from_karza(claimed_data)
            passport_obj.api_response = res
            api_data = json.loads(res)
            
            param['name'] = api_data['result']['name']['nameFromPassport'].lower() #+ ' ' + api_data['result']['name']['surnameFromPassport'].lower()
            # param['passport_no'] = api_data['result']['passportNumber']['passportNumberFromSource'].lower()
                
            return self.compare_fuzz(claimed_data, param, 90)

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    # def match_and_replace_param(self, param, ocr_string, result, img):
    #     try:
    #         if img == 'front':
    #             if fuzz.token_set_ratio(param['nameFromPassport'], ocr_string) >= 90:
    #                 result['nameFromPassport'] = param['nameFromPassport']            
    #             if fuzz.token_set_ratio(param['surnameFromPassport'], ocr_string) >= 90:
    #                 result['surnameFromPassport'] = param['surnameFromPassport']
    #             result['name'] = result['nameFromPassport'] + result['surnameFromPassport']
    #             result.pop('nameFromPassport')
    #             result.pop('surnameFromPassport')
    #         return result
    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return False
    
    def get_data_from_karza(self, result):
        try:
            url = app_settings.EXTERNAL_API['KARZAAPI_PASSPORT']
            karza_key = app_settings.EXTERNAL_API['KARZAAPI_KEY']
            karza_key_id = app_settings.EXTERNAL_API['KARZA_API_KEY_ID']
            headers = {karza_key_id: karza_key}
            dob = result['dob'].replace('-','/')
            payload = {
            "consent": "y",
            "fileNo": result['fileNo'],
            "dob": dob,
            }
            payload_str = json.dumps(payload)
            res = requests.post(url, data=payload_str, headers=headers)
            return res.text
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def get_passport_front_result(self, ocr_string):
        try:
            #passport number working perfect
            passport_list = {}
            passport_list['ocr_string'] = ocr_string
            input_str = ocr_string.replace('\n', ' ')
            input_str = input_str.replace('$', 'S')
            input_str = input_str.replace('  ', ' ')
            pno_reg = r'[A-Z][0-9][0-9]{6}'
            pno_match = re.search(pno_reg, input_str)
            if pno_match:
                passport_list['pno'] = pno_match.group() 
            else:
                return False

            #name working perfect
            input_str = ocr_string.lower()
            name_reg = r'k?ind<?<?[a-z]+<<?[a-z]+<?[a-z]*<'
            name_match = re.search(name_reg, input_str)
            if name_match:
                name = name_match.group() 
                name = name.split('<<')
                surname = name[0].replace('kind','').replace('ind','')
                firstname = name[1].replace('<<', '').replace('<', ' ').strip()
                passport_list['name'] = firstname + ' ' + surname

            #dob working perfect
            input_str = ocr_string.lower()
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
                passport_list['dob'] = datemin.strftime("%d-%m-%Y")
            return passport_list
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    def get_passport_back_result(self, ocr_string):
        try:
            #fileNo working perfectly
            passport_list = {}
            passport_list['ocr_string'] = ocr_string
            input_str = ocr_string.replace('\r','')
            file_reg = r'(\n[A-Z0-9]{7}[0-9]{8}\n)|(\n[A-Z0-9]{5}[0-9]{7}\n)'
            file_match = re.search(file_reg, input_str)
            if file_match:
                passport_list['fileNo'] = (file_match.group()).replace('\n','')
            elif  not passport_list['fileNo']:
                file_reg = r'No\n([A-Z0-9]+)' 
                match = re.search(file_reg, ocr_string)
                if match:
                    passport_list['fileNo'] = match.group(1)    
            else:
                return False

            #address working perfectly
            passport_list['address'] = ''
            address_reg = r'\n[ A-Z0-9:.!@#$%^&*();<>?\",_/\-]+\n[ A-Z0-9:.!@#$%^&*();<>?\",_/\-]+\n[ A-Z0-9:.!@#$%^&*();<>?\",_/\-]+\n'
            add_match = re.search(address_reg, input_str)
            if add_match:
                passport_list['address'] = (add_match.group()).replace('\n','')

            #father name working perfect
            passport_list['father_name'] = 'na'
            name_reg = r'\n[A-Z ]+\n'
            name_match = re.search(name_reg, input_str)
            if name_match:
                passport_list['father_name'] = (name_match.group()).replace('\n','')
            return passport_list
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

'''
Fetch the details from aadhaar front image string received from google ocr
fetch - name, gender, dob, adhaar number
'''
class AadhaarFrontProcessor():
    def process(self, ocr_string):
        try:
            aadhaar_dic = {}
            aadhaar_dic['ocr_string'] = ocr_string
            input_str = ocr_string.lower()
            
            #find aadhaar number
            reget = '[\n, ][0-9]{4}[ ]{0,2}[0-9]{4}[ ]{0,2}[0-9]{4}[\n ,]'
            match = re.search(reget, input_str)
            if match:
                match = match.group()
                aadhaar_dic['adhaar_number'] = match.replace('\n','').replace(',','').replace(' ','')
            else:
                return False
            
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
                aadhaar_dic['dob'] = datemin.strftime("%d-%m-%Y")
                aadhaar_dic['yob'] = False
            elif y_match:
                year_str = y_match.group()
                birth_year = r'[0-9]{4}'
                year_match = re.search(birth_year, year_str)
                dob_year = year_match.group() + '-01-01'
                aadhaar_dic['dob'] = dob_year
                aadhaar_dic['yob'] = True
            else:
                aadhaar_dic['dob'] = ''
            
            #find name
            try:
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
class AadhaarBackProcessor():

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
            response['ocr_string'] = ocr_string
            
            # Extract Address
            lst_split = ocr_string.split()
            english_words = []
            for word in lst_split:
                res = self.isEnglish(word)  
                if res == True:
                    english_words.append(word)

            string = ' '.join(english_words)
            string = string.lower()
            index = self.match_string(string)
            
            #find aadhaar number
            reget = '[ ][0-9]{4}[ ]{0,2}[0-9]{4}'
            match = re.search(reget, string[index:])
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
            try:
                pattern = r'[sdiwc/o०0:]{2,8}[ ]?[a-z0oO०]+[ ][a-z]*[ ]?[a-z]*[,.]'
                str_name = re.findall(pattern,string)
                if len(str_name) == 0:
                    response["father_name"] = ''
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
                return response
            except Exception as ex:
                traceback.print_exc()
                logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
            
            return response
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return None


class PanOcrProcessor():
    def process(self, ocr_string):
        data = {}
        try:
            data['ocr_string'] = ocr_string
            data['pan_number'] = re.search("[A-Z]{5}[0-9]{4}[A-Z]{1}", ocr_string).group()
            try:
                name_start_index = ocr_string.index('Name') + 5
                new_test = ocr_string[name_start_index:]
                name_end_index = new_test.find('\n') + name_start_index
                data['Name'] = ocr_string[name_start_index: name_end_index]
            except:
                try:
                    dt = ocr_string.encode("ascii", errors="ignore").decode()
                    dt = dt.replace('\n \n', '\n')
                    dt = dt.replace('\n\n\n', '\n')
                    name_start_index = dt.index('INDIA') + 6
                    new_test = dt[name_start_index:]
                    name_end_index = new_test.find('\n') + name_start_index
                    data['Name'] = dt[name_start_index: name_end_index]
                except:
                    data['Name'] = " "
            try:
                name_start_index = ocr_string.index('Name') + 5
                new_father_start = ocr_string[name_start_index:].index('Name') + 5 + name_start_index
                new_father_test = ocr_string[new_father_start:]
                name_father_end_index = new_father_test.find('\n') + new_father_start
                data['father_name'] = ocr_string[new_father_start: name_father_end_index]
            except:
                try:
                    dt = ocr_string.encode("ascii", errors="ignore").decode()
                    dt = dt.replace('\n \n', '\n')
                    dt = dt.replace('\n\n\n', '\n')
                    name_start_index = dt.index('INDIA') + 6
                    new_test = dt[name_start_index:].index('\n') + name_start_index
                    father_name_start = new_test + 1
                    name_end_index = dt[father_name_start:].find('\n') + father_name_start
                    data['father_name'] = dt[father_name_start: name_end_index]
                except:
                    data['father_name'] = " "
            try:
                data["dob"] = re.findall('\d{2}/\d{2}/\d{4}', ocr_string)[0].replace('/', '-')
            except:
                data["dob"] = None
            return data
        except:
            return data