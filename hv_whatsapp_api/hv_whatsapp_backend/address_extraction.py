import json
from . import check_processor as cp
import re
import logging
import inspect
from datetime import datetime
import traceback

logging.basicConfig(filename="error_log.log")

'''
This class do the address extraction functionality from different addresses
'''
class AddressExtractor():
    from .name_permutor import name_genrator       

    '''
    This function is used to get the district code from 
    IndiaDistrict json based on the district name
    '''
    def get_district_mapping(self, district_name):
        try:
            district_name = district_name.lower()
            obj = open("hv_whatsapp_api//hv_whatsapp_backend//IndianDistrict.json")
            district = json.load(obj)
            data = district["data"]
            if district_name in str(data).lower():
                district_code = next( item for item in data if district_name in item["name"].lower())
                district_code = district_code["code"]
            else:
                district_code = ''
            return district_code
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    This function is used to get the state code from 
    IndianStates json based on the state name
    '''
    def get_state_mapping(self, state_name):
        try:
            obj = open("hv_whatsapp_api//hv_whatsapp_backend//IndianStates.json")
            state = json.load(obj)
            if state_name.lower() in str(state).lower():
                try:
                    state_code = list(state.keys())[list(state.values()).index(state_name.title())]
                except Exception as ex:
                    state_code = ''    
            else:
                state_code = ''
            return state_code
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    This function is used to create the address 
    by combining the postal address json
    '''
    def create_address(self,address):
        try:
            house = str(address["house"])
            floor = address["floor"]
            building = address["building"]
            complex_name = address["complex"]
            street = address["street"]
            local_area = address["local_area"]
            untagged = address["Untagged"]
            district = address["district"]
            state = address["state"]
            pin = str(address["pin"])
            blk_sec = str(address["blk_sec"])
            space = " "

            comb_address = house + space + floor + space + blk_sec + space + building + space +\
                            complex_name + space + street + space + local_area + \
                                space + untagged + space + district + space + state + space + pin
            comb_address = re.sub(r'[.]+', '', comb_address)
            comb_address = re.sub(r'[.,/\-]+', ' ', comb_address)
            comb_address = re.sub(r'[ ]+', ' ', comb_address)
            return comb_address
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    This function is used to get the uncommon address substring 
    from postal address and original address 
    '''
    def uncommon(self, postal_address,original_address): 
        try:
            a = self.create_address(postal_address).lower()
            original_address = re.sub(r'[.]+', '', original_address)
            original_address = re.sub(r'[,./\:-]', ' ', original_address)
            b = re.sub(r'[ ]+', ' ', original_address).lower()
            a=a.split() 
            b=b.split() 
            k=' '.join(set(a).symmetric_difference(set(b)))
            return k 
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    Remove the duplicate substring from the address
    '''
    def remove_duplicates_from_postal_address(self, address):
        try:
            temp = {val : key for key, val in address.items()} 
            res = {val : key for key, val in temp.items()}
            return res
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    Remove the directions name (east,west,north,south) from the address
    '''
    def remove_directions(self, user_details):
        try:
            user_details['local_area'] = user_details['local_area'].lower()
            user_details['Untagged'] = user_details['Untagged'].lower()
            user_details['street'] = user_details['street'].lower()
            user_details['building'] = user_details['building'].lower()
            user_details['complex'] = user_details['complex'].lower()
            user_details['blk_sec'] = user_details['blk_sec'].lower()
            user_details['floor'] = user_details['floor'].lower()
            user_details['extra'] = user_details['extra'].lower()
            user_details['district'] = user_details['district'].lower()
            user_details['state'] = user_details['state'].lower()
            user_details['district_code'] = user_details['district_code'].lower()
            user_details['state_code'] = user_details['state_code'].lower()
            user_details['local_area'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['local_area']).strip()
            user_details['Untagged'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['Untagged']).strip()
            user_details['street'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['street']).strip()
            user_details['building'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['building']).strip()
            user_details['complex'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['complex']).strip() 
            user_details['blk_sec'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['blk_sec']).strip() 
            user_details['floor'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['floor']).strip() 
            user_details['extra'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['extra']).strip() 
            user_details['district'] = re.sub(r'(east)|(west)|(north)|(south)','',user_details['district']).strip() 
            user_details['local_area'] = user_details['local_area'].replace(user_details['district'], '').replace(user_details['state'], '').replace(user_details['district_code'], '').replace(user_details['state_code'], '')
            user_details['Untagged'] = user_details['Untagged'].replace(user_details['district'], '').replace(user_details['state'], '').replace(user_details['district_code'], '').replace(user_details['state_code'], '')
            user_details['street'] = user_details['street'].replace(user_details['district'], '').replace(user_details['state'], '').replace(user_details['district_code'], '').replace(user_details['state_code'], '')
            user_details['building'] = user_details['building'].replace(user_details['district'], '').replace(user_details['state'], '').replace(user_details['district_code'], '').replace(user_details['state_code'], '')
            user_details['complex'] = user_details['complex'].replace(user_details['district'], '').replace(user_details['state'], '').replace(user_details['district_code'], '').replace(user_details['state_code'], '')
            user_details['blk_sec'] = user_details['blk_sec'].replace(user_details['district'], '').replace(user_details['state'], '').replace(user_details['district_code'], '').replace(user_details['state_code'], '')
            user_details['floor'] = user_details['floor'].replace(user_details['district'], '').replace(user_details['state'], '').replace(user_details['district_code'], '').replace(user_details['state_code'], '')
            user_details['extra'] = user_details['extra'].replace(user_details['district'], '').replace(user_details['state'], '').replace(user_details['district_code'], '').replace(user_details['state_code'], '')
            if len(user_details['extra']) < 3:
                user_details['extra'] = ''
            # print('user detail-----', user_details)
            return user_details
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    Breaking address into parts based on locality, house no, etc...
    '''
    def get_address_breakup(self, address, str_address): #70
        try:
            add = address
            addr = {}
            addr['blk_sec'] = ''
            addr['state'] = add.get('State', '')
            # get state code
            addr['state_code'] = self.get_state_mapping(addr['state'])
            if addr['state_code']:
                addr['state_code'] = ' '+ addr['state_code'] +' '
            addr['district'] = add.get('District', '')
            if 'delhi' in addr['district'].lower():
                addr['district'] = 'DELHI'
            # get district code
            addr['district_code'] = self.get_district_mapping(addr['district'])
            if addr['district_code']:
                addr['district_code'] = ' '+ addr['district_code'] +' '
            addr['local_area'] = add.get('locality', '')
            addr['Untagged'] = add.get('Untagged', '')
            addr['house'] = add.get('House', '')
            if ',' in addr['house']:
                h_split = addr['house'].split(',')
                a1 = h_split[0].lower().strip()
                a2 = h_split[1].lower().strip()
                if 'block' in a1 or 'sector' in a1:
                    addr['blk_sec'] = a1
                    a2 = re.sub(r'[ /\,.|-]','',a2)
                    match = re.search(r'[0-9]{1,8}', a2)
                    if match:
                        addr['house'] = match.group()
                elif 'block' in a2 or 'sector' in a2:
                    addr['blk_sec'] = a2
                    a1 = re.sub(r'[ /\,.|-]','',a1)
                    match = re.search(r'[0-9]{1,8}', a1)
                    if match:
                        addr['house'] = match.group()
                else:
                    hno_addr = re.sub(r'[ /\,.|-]','',str_address)
                    match = re.search(r'[@a-z]{0,15}[0-9]{1,8}', hno_addr)
                    if match:
                        match = re.search(r'[0-9]{1,8}', match.group())
                        if match:
                            addr['house'] = match.group()
                        else:
                            addr['house'] = ''
            else:
                addr['house'] = re.sub(r'[ /\,.|-]','',addr['house'])
                match = re.search(r'[0-9]{1,8}', addr['house'])
                if match:
                    addr['house'] = match.group()
            match = re.search(r'[0-9]{1,5}[ /,-]?[0-9]{0,5}', addr['house'].lower())
            if match:
                len_add = len(str_address)
                temp_address = re.sub(r'[ ,.:/\|-]','', str_address[0:(len_add-10)])
                if match.group().lower().strip() in temp_address.lower():
                    pass
                else:
                    addr['house'] = ''
            addr['pin'] = add.get('Pin', '')
            addr['street'] = add.get('Street', '')
            addr['building'] = add.get('Building', '')
            addr['complex'] = add.get('Complex', '')
            addr['floor'] = add.get('Floor', '')
            address_str = self.uncommon(addr, str_address)
            address_str = re.sub(r'(house)|(h.no.)|(sec[tor]{0,3})|(sector[s]?)|(block[s]?)|(blk[s]?)|(teh[sil.]{0,4})|(vil[lage]{0,4})|(dist[trict]{0,5})','', address_str)
            if address_str:
                addr['extra'] = address_str.strip()
            else:
                addr['extra'] = ''
            dic2 = self.remove_duplicates_from_postal_address(addr)
            dic2.update(addr)
            dic2 = self.remove_directions(dic2)
            return dic2

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    getting the possible name in combination of
    candidate and father name
    '''
    def get_possible_names(self, name, father_name):
        try:
            from .name_permutor import name_genrator
            name_obj = name_genrator(name,father_name)
            return name_obj.get_all_name_permutations()
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    creating json of address breakup, original address, name,
    father name, possible names and age of the candidate
    '''
    def break_address_in_parts(self, address_obj):      
        try:  
            add = address_obj
            add = add['result']['address1']
            
            add = self.get_address_breakup(add, address_obj['address'])
            add['address'] = address_obj['address']
            name = address_obj['applicant_name'].split()
            add['name'] = name #for filtering
            add['father_name'] = address_obj['father_name']
            
            applicant_name, father_name = address_obj['applicant_name'], address_obj['father_name']

            #combining criminal name with id name
            if address_obj.get('id_candidate_name', None) and (address_obj['applicant_name'] != address_obj['id_candidate_name']):
                applicant_name = address_obj['applicant_name'].split(' ')
                address_obj['id_candidate_name'] = address_obj['id_candidate_name'].split(' ')
                applicant_name = list(set(applicant_name + address_obj['id_candidate_name']))
                applicant_name = ' '.join(applicant_name)
            
            # # #combining criminal father name with id father name
            if address_obj.get('id_father_name', None) and (address_obj['father_name'] != address_obj['id_father_name']):
                father_name = address_obj['father_name'].split(' ')
                address_obj['id_father_name'] = address_obj['id_father_name'].split(' ')
                father_name = list(set(father_name + address_obj['id_father_name']))
                father_name = ' '.join(father_name)

            #for removing duplicates
            add['possible_names'] = self.get_possible_names(applicant_name, father_name)
            add['age'] = address_obj['age']
            return add
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex