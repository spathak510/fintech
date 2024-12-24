from hv_whatsapp_api import models as Model
import json
from . import check_processor
import requests 
import re
from bs4 import BeautifulSoup 
import logging
import inspect
import traceback
import datetime
from hv_whatsapp import settings as app_settings
from geopy.distance import geodesic
from hv_whatsapp_api.utils import number_masking

logging.basicConfig(filename="error_log.log")

'''
Input for all the functions is a payload(session_id, order_id)
'''
class Report():

    def __init__(self):
        self.date_obj = check_processor.BaseCheckProcessor()
        self.header = {}
        self.dl = {}
        self.adhaar = {}
        self.crime = {}
        self.emp = {}
        self.kyc = {}
        self.final = {}


    '''
    create json for report headers
    '''
    def json_for_header(self,payload):
        try:
            print("INSIDE HEADER REPORT")
            header = {}
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)
            lookup_model = Model.customer_lookup.objects.filter(customer_info = session_id).last()

            if check_model.customer_type == '2' or check_model.customer_type == '3':
                header["client_name"] = lookup_model.vendor_name.upper()
                header["client_mob"] = number_masking(lookup_model.vendor_mobile)
                # report date
                import datetime
                cur_date = datetime.datetime.now().strftime("%d-%m-%Y")
                header["report_date"] = str(cur_date)
                header["applicant_name"] = lookup_model.candidate_name.upper()
                header["applicant_phone"] = number_masking(lookup_model.candidate_mobile)
                header["appicant_address"] = check_model.address.upper()
            else:
                header["client_name"] = check_model.name.upper()
                header["client_mob"] = number_masking(check_model.mobile_no)
                # report date
                import datetime 
                cur_date = datetime.datetime.now().strftime("%d-%m-%Y")
                header["report_date"] = str(cur_date)
                header["applicant_name"] = check_model.name.upper()
                header["applicant_phone"] = number_masking(check_model.mobile_no)
                header["appicant_address"] = check_model.address.upper()
            
            

            self.header = header

            return header
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json for dl data in report
    '''
    def json_for_dl_report(self, payload):
        try:
            print("INSIDE DRIVING LICENCE REPORT")
            dl_report = {}
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)

            dl_report["applicant_mobile"] = number_masking(check_model.mobile_no)
            
            dob = check_model.dob
            dob = dob.strftime("%d-%m-%Y")
            dl_report["dob"] = dob
            # fetch dl check result
            order_id = payload["order_id"]
            check_dl_model = Model.dl_result.objects.get(order = order_id)

            dl_report["is_check_passed"] = check_dl_model.is_check_passed
            dl_report["color_code"] = check_dl_model.color_code
            update_date = self.date_obj.get_date_for_karza(check_dl_model.updated_at)
            dl_report['update_date'] = update_date
            # fetch api result
            api_result = json.loads(check_dl_model.api_result)
            api_result = api_result['result']
            dl_report["applicant_name"] = api_result["name"].upper()
            dl_report["father_name"] = api_result["father/husband"].upper()
            dl_report["applicant_address"] = api_result["address"].upper()
            dl_report["dl_number"] = api_result["dl_number"]
            dl_report["issue_date"] = api_result["issue_date"]
            # base64 to image
            import base64
            if api_result["img"] == '':
                filename = 'static/img/img_no.png'
                dl_report["image"] = 'noimg'
            else:
                img_name = str(session_id) + '.jpg'
                imgstring = api_result["img"]
                imgdata = base64.b64decode(imgstring)
                filename = 'static/img/' + img_name  # I assume you have a way of picking unique filenames
                with open(filename, 'wb') as f:
                    f.write(imgdata)
                dl_report["image"] = 'img'
                dl_report["img_name"] = img_name
            from PIL import Image
            try:
                foo = Image.open(filename)
                foo = foo.resize((140,180),Image.ANTIALIAS)
                foo.save(filename,optimize=True,quality=95)
            except Exception:
                pass    
            dl_report["blood"] = api_result["blood_group"]

            # set front and back image
            check_ocr_model = Model.ocr_response.objects.get(customer_info = session_id)

            dl_report["front_image"] = check_ocr_model.front_image_url
            dl_report["back_image"] = check_ocr_model.back_image_url
            update_date = datetime.datetime.now()
            dl_report["remark"] = update_date.strftime('%d %B %Y')
            self.dl = dl_report
            return dl_report

        except Exception as ex:
            # print(str(ex))
            # print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json for DL Badge data in report
    '''
    def json_for_dl_badge(self, payload):
        try:
            print("INSIDE DRIVING LICENCE REPORT")
            order_id = payload["order_id"]
            dl_report = {}
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)
            dl_report["dob"] = (check_model.dob).strftime("%d-%m-%Y")
            selfie_url = check_model.selfie_url
            # dl_report["selfie_url"] = selfie_url
            
            #downloading selfie
            # https://checkapi.helloverify.com/static/img/dl_red.png
            import requests
            img_name = "static/img/" + order_id + ".jpg"
            img_data = requests.get(selfie_url).content            
            with open(img_name, 'wb') as handler:
                handler.write(img_data)
            
            dl_report["selfie_url"] = "https://checkapi.helloverify.com/" + img_name

            # fetch dl check result            
            check_dl_model = Model.dl_result.objects.get(order = order_id)
            dl_report["is_check_passed"] = check_dl_model.is_check_passed
            # fetch api result
            api_result = json.loads(check_dl_model.api_result)
            api_result = api_result['result']
            dl_report["applicant_name"] = api_result["name"].upper()
            dl_report["father_name"] = api_result["father/husband"].upper()
            dl_report["dl_number"] = api_result["dl_number"]
            dl_report["badge_id"] = payload['order_id']
            dl_report["badge_url"] = 'https://hellov.in/app/badge?id='+payload['order_id']
                        
            verification_date = datetime.datetime.now()
            expiry_date = verification_date.replace(year = verification_date.year + 1)
            dl_report["verification_date"] = verification_date.strftime('%d %B %Y')
            dl_report["expiry_date"] = expiry_date.strftime('%b %d %Y %H:%M:%S')
            
            self.dl = dl_report
            return dl_report

        except Exception as ex:
            # print(str(ex))
            # print(traceback.print_exc())
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json for crime data in report
    '''
    def json_for_crime_report(self, payload):
        try:
            print("INSIDE CRIMINAL REPORT")
            crime_report = {}
            session_id = payload["session_id"]

            check_model = Model.customer_info.objects.get(session_id = session_id)

            crime_report["applicant_name"] = check_model.name.upper()
            crime_report["applicant_mobile"] = number_masking(check_model.mobile_no)
            crime_report["applicant_address"] = check_model.address.upper()
            dob = check_model.dob
            ocr_obj = Model.ocr_response.objects.get(customer_info = session_id)
            if 'true,' in ocr_obj.front_parse_result:
                dob = dob.strftime("%Y")
            else:
                dob = dob.strftime("%d-%m-%Y")
            crime_report["dob"] = dob
            crime_report["father_name"] = check_model.father_name.upper()
            
            # fetch crime check result
            order_id = payload["order_id"]
            check_crime_model = Model.criminal_result.objects.get(order = order_id)       

            if check_crime_model.color_code == 0:
                crime_report["color_code"] = check_crime_model.color_code
            else:       
                crime_report["color_code"] = check_crime_model.manual_color_code

            crime_report["is_check_passed"] = check_crime_model.is_check_passed

            if check_crime_model.is_check_passed:
                crime_report["record_found"] = " no"
            else:
                crime_report["record_found"] = ''

            update_date = datetime.datetime.now()
            crime_report["remark"] = update_date.strftime('%d %B %Y')
            self.crime = crime_report

            return crime_report
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json for aadhaar data in report
    '''
    def json_for_adhaar_report(self, payload):
        try:
            print("INSIDE ADHAAR REPORT")
            adhaar_report = {}
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)
            
            adhaar_report["applicant_name"] = (check_model.name).upper()
            adhaar_report["applicant_mobile"] = number_masking(check_model.mobile_no)
            adhaar_report["applicant_address"] = (check_model.address).upper()
            adhaar_report["address_len"] = len(check_model.address)
            adhaar_report["adhaar_number"] = number_masking(check_model.adhaar_number)
            dob = check_model.dob
            ocr_obj = Model.ocr_response.objects.get(customer_info = session_id)
            if 'true,' in ocr_obj.front_parse_result:
                dob = dob.strftime("%Y")
            else:
                dob = dob.strftime("%d-%m-%Y")
            adhaar_report["dob"] = dob
            adhaar_report["father_name"] = (check_model.father_name).upper()

            # fetch adhaar check result
            order_id = payload["order_id"]
            check_adhaar_model = Model.adhaar_result.objects.get(order = order_id)

            adhaar_report["is_check_passed"] = check_adhaar_model.is_check_passed
            update_date = self.date_obj.get_date_for_karza(check_adhaar_model.updated_at)
            adhaar_report['update_date'] = update_date
            adhaar_report["color_code"] = check_adhaar_model.color_code

            # validation of data
            api_response = json.loads(check_adhaar_model.rule_engine_result)
            api_result = json.loads(check_adhaar_model.api_result)

            adhaar_report["number_valid"] = "Green" if api_response["uid"] else "Red"
            adhaar_report["age_valid"] = "Green" if api_response["age_range"] else "Red"
            adhaar_report["gender_valid"] = "Green" if api_response["gender"] else "Red"
            adhaar_report["state_valid"] = "Green" if api_response["state"] else "Red"
            adhaar_report["dob_valid"] = "Green" if api_response["dob"] else "Red"

            # valid data
            adhaar_report["uid_data"] = api_result["statusMessage"].replace(' Exists', '')
            adhaar_report["age_data"] = api_result["ageBand"]
            adhaar_report["mobile_data"] = api_result["maskedMobileNumber"] if api_result["maskedMobileNumber"] else ""
            adhaar_report["state_data"] = api_result["address"].upper()
            adhaar_report["gender_data"] = api_result["gender"].upper()
            adhaar_report["pin_data"] = api_result["pincode"]

            # set front and back image for KYC
            # check_ocr_model = Model.ocr_response.objects.get(customer_info = session_id)

            # adhaar_report["front_image"] = check_ocr_model.front_image_url
            # adhaar_report["back_image"] = check_ocr_model.back_image_url
            update_date = datetime.datetime.now()
            adhaar_report["remark"] = update_date.strftime('%d %B %Y')
            self.adhaar = adhaar_report
            return adhaar_report
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json for aadhaar data in report
    '''
    def json_for_adhaar_badge(self, payload):
        try:
            print("INSIDE ADHAAR REPORT")
            adhaar_report = {}
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)
            
            adhaar_report["applicant_name"] = (check_model.name).upper()
            adhaar_report["adhaar_number"] = number_masking(check_model.adhaar_number)
            import requests
            order_id = payload["order_id"]
            selfie_url =  check_model.selfie_url
            img_name = "static/img/" + order_id + ".jpg"
            img_data = requests.get(selfie_url).content            
            with open(img_name, 'wb') as handler:
                handler.write(img_data)
            
            adhaar_report["selfie_url"] = "https://checkapi.helloverify.com/" + img_name
            # adhaar_report["selfie_url"] = 'https://checkapi.helloverify.com/static/img/img.jpg'
            dob = check_model.dob
            ocr_obj = Model.ocr_response.objects.get(customer_info = session_id)
            if 'true,' in ocr_obj.front_parse_result:
                dob = dob.strftime("%Y")
            else:
                dob = dob.strftime("%d-%m-%Y")
            adhaar_report["dob"] = dob
            adhaar_report["father_name"] = (check_model.father_name).upper()

            # fetch adhaar check result
            order_id = payload["order_id"]
            check_adhaar_model = Model.adhaar_result.objects.get(order = order_id)
            adhaar_report["is_check_passed"] = check_adhaar_model.is_check_passed

            # validation of data
            api_response = json.loads(check_adhaar_model.rule_engine_result)
            api_result = json.loads(check_adhaar_model.api_result)

            adhaar_report["number_valid"] = "Green" if api_response["uid"] else "Red"
            adhaar_report["age_valid"] = "Green" if api_response["age_range"] else "Red"
            adhaar_report["gender_valid"] = "Green" if api_response["gender"] else "Red"
            adhaar_report["state_valid"] = "Green" if api_response["state"] else "Red"

            # valid data
            adhaar_report["uid_data"] = api_result["statusMessage"].replace(' Exists', '')
            adhaar_report["age_data"] = api_result["ageBand"]
            adhaar_report["state_data"] = api_result["address"].upper()
            adhaar_report["gender_data"] = api_result["gender"].upper()
            adhaar_report["badge_id"] = payload['order_id']
            adhaar_report["badge_url"] = 'https://hellov.in/app/badge?id='+payload['order_id']
            
            verification_date = datetime.datetime.now()
            expiry_date = verification_date.replace(year = verification_date.year + 1)
            adhaar_report["verification_date"] = verification_date.strftime('%d %B %Y')
            adhaar_report["expiry_date"] = expiry_date.strftime('%b %d %Y %H:%M:%S')

            self.adhaar = adhaar_report
            return adhaar_report
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)
    '''
    create json for employment data in report
    '''
    def json_for_emp_report(self, payload):
        try:
            print("INSIDE EMPLOYMENT REPORT")
            emp_report = {}
            count_doj = 0
            session_id = payload["session_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)

            emp_report["applicant_name"] = (check_model.name).upper()
            emp_report["applicant_mobile"] = number_masking(check_model.mobile_no)
            emp_report["uan_number"] = check_model.uan
            emp_report["father_name"] = (check_model.father_name).upper()

            # fetch uan check result
            order_id = payload["order_id"] #review below old code
            uan_obj = Model.uan_result.objects.get(order = order_id)

            update_date = datetime.datetime.now()
            emp_report['update_date'] = update_date.strftime('%d-%m-%Y')
            
            org_details = json.loads(uan_obj.org_details)

            emp_report["org_detail"] = org_details

            emp_report['validation_date'] = update_date.strftime('%d-%m-%Y')
            emp_report["remark"] = update_date.strftime('%d %B %Y')
            self.emp = emp_report
            return emp_report

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


    # def json_for_emp_report_temp(self, payload):
    #     try:
    #         print("INSIDE EMPLOYMENT REPORT")
    #         emp_report = {}
    #         count_doj = 0
    #         session_id = payload["session_id"]
    #         check_model = Model.customer_info.objects.get(session_id = session_id)

    #         emp_report["applicant_name"] = (check_model.name).upper()
    #         emp_report["applicant_mobile"] = check_model.mobile_no
    #         emp_report["uan_number"] = check_model.uan
    #         emp_report["father_name"] = (check_model.father_name).upper()

    #         # fetch uan check result
    #         order_id = payload["order_id"]
    #         check_emp_model = Model.check_uan_result.objects.filter(order_id = order_id).last()
    #         update_date = self.date_obj.get_date_for_karza(check_emp_model.updated_at)
    #         emp_report['update_date'] = update_date

    #         emp_detail = json.loads(check_emp_model.api_result)
    #         org_detail = emp_detail["result"]["employers"]
    #         detail = []
    #         for item in org_detail:
    #             dic = {}
    #             dic["org_name"] = item["establishmentName"].upper()
    #             dic["doj"] = datetime.datetime.strptime(item["dateOfJoining"], '%Y-%m-%d').strftime('%d-%m-%Y')

    #             # date of exit
    #             if item["dateOfExit"] == None:
    #                 dic["dol"] = 'NA'
    #                 if count_doj > 0:
    #                     dic["dol"] = 'Not Disclosed'
    #                     count_doj = 0
    #                 else:
    #                     count_doj += 1
    #             else:
    #                 dic["dol"] = datetime.datetime.strptime(item["dateOfExit"], '%Y-%m-%d').strftime('%d-%m-%Y')
                    

    #             # address
    #             dic["address"] = item["address"]["address"]+', '+\
    #                             str(item["address"]["city"])+', '+ str(item["address"]["state"])+'- '+\
    #                             str(item["address"]["pincode"])
    #             dic["address"] = (dic["address"].replace('None', '')).upper()
    #             detail.append(dic)
    #         emp_report["org_detail"] = detail

    #         update_date = datetime.datetime.now()
    #         emp_report['validation_date'] = update_date.strftime('%d-%m-%Y')
    #         emp_report["remark"] = update_date.strftime('%d %B %Y')
    #         self.emp = emp_report
    #         return emp_report

    #     except Exception as ex:
    #         traceback.print_exc()
    #         logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
    #         logging.exception((inspect.currentframe().f_code.co_name).upper())
    #         return str(ex)

    def find_lat_long(self, current_address):
        try:
            import requests
            map_url = app_settings.EXTERNAL_API['MAP_URL']
            map_key = app_settings.EXTERNAL_API['MAP_KEY']

            req_url = map_url + current_address + '&key=' + map_key
            res = requests.get(req_url)

            location_json = res.json()
            lat = location_json['results'][0]['geometry']['location']['lat']
            lng = location_json['results'][0]['geometry']['location']['lng']
            claimed_lat_lng = str(lat) + ',' + str(lng)
            return claimed_lat_lng

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    def find_location_match(self, claimed_lat_long, actual_lat_long):
        try:
            import requests
            map_img_url = app_settings.EXTERNAL_API['MAP_IMG_URL']
            map_key = app_settings.EXTERNAL_API['MAP_KEY']
            map_img_url = map_img_url.format(point1 = claimed_lat_long, point2 = actual_lat_long) + '&key=' + map_key
            
            distance = geodesic(claimed_lat_long, actual_lat_long).meters
            distance = round(distance, 2)
            if distance > 300:
                location_match = "false"
            else:
                location_match = "true"
            
            return map_img_url, location_match, distance
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json for ssl check report
    ''' 
    def json_for_ssl_check_report(self, payload):
        from hv_whatsapp.common_methods import resize_image
        try:
             print("INSIDE SSL CHECK REPORT")
             ssl_report = {}
             size = (200, 200)
             base_path_local = 'static/img/'
             session_id = payload["session_id"]
             sslcheck_obj = Model.SSLChekDetails.objects.filter(customer_info__session_id = session_id).last()
             selfie_key = sslcheck_obj.selfie_url.name
             output_image_path = base_path_local+(selfie_key.split('/')[-1])
             ssl_report['selfie'] = resize_image(selfie_key, output_image_path, size)
             signature_key = sslcheck_obj.signature_url.name
             output_image_path = base_path_local+(signature_key.split('/')[-1])
             ssl_report['signature'] = resize_image(signature_key, output_image_path, size)
             location_key =sslcheck_obj.location_img_url.name
             output_image_path = base_path_local+(location_key.split('/')[-1])
             ssl_report['location_img_url'] = resize_image(location_key, output_image_path, size)
             return ssl_report
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json for employment data in report
    '''
    def json_for_kyc_report(self, payload):
        try:
            print("INSIDE DRIVING LICENCE REPORT")
            kyc_report = {}
            session_id = payload["session_id"]
            kyc_model = Model.kyc_report_data.objects.get(customer_info = session_id)
            kyc_report['stay_from'] = (kyc_model.stay_from).strftime("%d-%m-%Y")
            kyc_report['stay_to'] = (kyc_model.stay_to).strftime("%d-%m-%Y")
            kyc_report['ownership_status'] = (kyc_model.ownership_status).title()
            kyc_report['selfie_url'] = kyc_model.selfie_url
            kyc_report['gate_url'] = kyc_model.gate_url
            kyc_report['vehicle_or_sign_url'] = kyc_model.vehicle_or_sign_url
            kyc_report['front_img_url'] = kyc_model.front_img_url
            kyc_report['back_img_url'] = kyc_model.back_img_url
            kyc_report['claimed_address'] = kyc_model.current_address

            claimed_lat_long = self.find_lat_long(kyc_model.current_address)
            kyc_report['location_img_url'], kyc_report['location_match'], kyc_report['distance'] = self.find_location_match(claimed_lat_long, kyc_model.actual_lat_long)
            # print(kyc_report)
            kyc_model.claimed_lat_long = claimed_lat_long
            kyc_model.location_img_url = kyc_report['location_img_url']
            kyc_model.save()
            
            self.kyc = kyc_report
            return kyc_report

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


    '''
    get package name
    '''
    def get_package_name(self, session_id):
        try:
            cust_model = Model.customer_info.objects.get(session_id = session_id)
            customer_type = cust_model.customer_type
            service_type_id = cust_model.service_type_id

            service_model = Model.service_detail.objects.filter(customer_type = customer_type,service_type_id = service_type_id).last()
            package_name = service_model.service_type_name

            split_package = package_name.split('-')

            verify = split_package[0].strip()
            package = split_package[1].replace('.','').strip()

            cap_verify = verify.upper()
            cap_package = package.upper()

            return [cap_verify,cap_package]
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create final json for report 
    '''
    def final_result(self, payload):
        try:
            print("INSIDE FINAL REPORT")
            final_result = {}
            session_id = payload["session_id"]
            order_id = payload["order_id"]
            check_model = Model.customer_info.objects.get(session_id = session_id)

            id_type = check_model.id_type
            if id_type == '2':
                # fetch dl result
                check_dl_model = Model.dl_result.objects.get(order = order_id)
                id_check = check_dl_model.is_check_passed
                final_result["id_type"] = "DRIVING LICENCE"
            else:
                # fetch adhaar result
                check_adhaar_model = Model.adhaar_result.objects.get(order = order_id)
                id_check = check_adhaar_model.is_check_passed
                final_result["id_type"] = "AADHAAR CARD"

            if check_model.service_type_id == 2:
                # fetch uan result
                # check_uan_model = Model.check_uan_result.objects.filter(order_id = order_id).last()
                # uan_check = check_uan_model.is_check_passed
                uan_check = True


            # final calculation
            if id_check:
                final_result["id_result"] = "Green"
            else:
                final_result["id_result"] = "Red"
            check_crime_model = Model.criminal_result.objects.filter(order = order_id).last()
            if check_crime_model:
                crime_check = check_crime_model.is_check_passed
                if crime_check:
                    final_result["crime_result"] = "Green"
                else:
                    final_result["crime_result"] = "Red"

                if check_model.service_type_id == 2:
                    if True: #temp
                        final_result["uan_result"] = "Green"
                    else:
                        pass
                        # final_result["uan_result"] = "Red"
                if check_model.service_type_id == 2:                
                    if id_check and crime_check and uan_check:
                        final_result["final_result"] = "Green"
                    else:
                        final_result["final_result"] = "Red"
                else:
                    if id_check and crime_check:
                        final_result["final_result"] = "Green"
                    else:
                        final_result["final_result"] = "Red"
            else:
                if id_check:
                    final_result["final_result"] = "Green"
                else:
                    final_result["final_result"] = "Red"
            # get package name
            package_detail = self.get_package_name(session_id)
            final_result["verify"] = package_detail[0]
            final_result["package_name"] = package_detail[1]

            self.final = final_result
            
            return final_result
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    get case link for the criminal record
    '''
    def get_case_link(self, sid):
        try:
            session_id = sid
            order_obj = Model.order.objects.get(customer_info = session_id)
 
            order_id = order_obj.order_id
            check_crime_model = Model.criminal_result.objects.get(order = order_id)
            if check_crime_model.manual_color_code == '2':
                api_response = json.loads(check_crime_model.manual_response)
            else:    
                api_response = json.loads(check_crime_model.rule_engine_result)
            if len(api_response) == 0:
                link = ''
            else:
                link = api_response[0]["caseDetailsLink"]
            return link
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    create json for crime detail data from scrapped case link
    '''
    def get_crime_json(self, payload):
        try:
            sid = payload['session_id']
            URL = self.get_case_link(sid)
            if URL == '':
                return {}
            r = requests.get(URL) 
            soup = BeautifulSoup(r.content, 'html5lib') 
            get_res = r'{"status":.*};'
            st = re.search(get_res, str(soup))
            crime_res = st.group()
            crime_res = crime_res.replace(';','')
            dic_res = json.loads(crime_res)
            final_dic = {}
            final_dic['courtname'] = dic_res['details'][0]['courtName']
            final_dic['casetypename'] = dic_res['details'][0]['caseTypeName']
            final_dic['filingnumber'] = dic_res['details'][0]['filingNumber']
            final_dic['regnumber'] = dic_res['details'][0]['regNumber']
            final_dic['cinnumber'] = dic_res['details'][0]['cinNumber']
            final_dic['filingdate'] = dic_res['details'][0]['filingDate']
            final_dic['regdate'] = dic_res['details'][0]['caseRegDate']
            final_dic['hearingdate'] = dic_res['details'][0]['hearingDate']
            final_dic['courtnumberandjudge'] = dic_res['details'][0]['courtNumberAndJudge']
            # final_dic['petitioneraddress'] = dic_res['details'][0]['petitionerAddress']
            # final_dic['petitioneraddress'] = re.sub(r'\s*\\u00a0\s*', '', dic_res['details'][0]['petitionerAddress'])
            final_dic['petitioneraddress'] = dic_res['details'][0]['petitionerAddress'].replace('\u00c2\u00a0', ' ')
            # final_dic['respondentaddress'] = dic_res['details'][0]['respondentAddress']
            # final_dic['respondentaddress'] = re.sub(r'\s*\\u00a0\s*', '', dic_res['details'][0]['respondentAddress'])
            final_dic['respondentaddress'] = dic_res['details'][0]['respondentAddress'].replace('\u00c2\u00a0', ' ')
            final_dic['underact'] = dic_res['details'][0]['underAct']
            final_dic['undersection'] = dic_res['details'][0]['underSection']
            if dic_res['details'][0]['original_caseFlow']:
                final_dic['caseflow'] = (dic_res['details'][0]['original_caseFlow']).replace('[','').replace(']', '').split(',')
                final_dic['caseflow_len'] = len(final_dic['caseflow'])-1
            else:
                final_dic['caseflow'] = ''
                final_dic['caseflow_len'] = ''
            return final_dic
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    create json of all the checks and save in database
    '''
    def create_report(self,payload):
        try:
            session_id = payload["session_id"]
            cust_model = Model.customer_info.objects.get(session_id = session_id)
            order_obj = Model.order.objects.get(customer_info = session_id)
            service_model = Model.service_detail.objects.filter(customer_type = cust_model.customer_type, service_type_id=cust_model.service_type_id).last()
            check_name = Model.check_types(service_model.check_types).name            
            id_type = cust_model.id_type

            jsn = {}            
            if id_type == '1':
                if 'id_badge' == check_name:
                    jsn["adhaar"] = self.json_for_adhaar_badge(payload)
                else:    
                    jsn["adhaar"] = self.json_for_adhaar_report(payload)
            else:
                if 'id_badge' == check_name:
                    jsn["dl"] = self.json_for_dl_badge(payload)
                else:                    
                    jsn["dl"] = self.json_for_dl_report(payload)
                    
            if 'id_crime_check' in check_name and service_model.service_type_id == 29:
                jsn['sslcheck'] = self.json_for_ssl_check_report(payload)        
            
            if 'kyc' in check_name:
                jsn['kyc'] = self.json_for_kyc_report(payload)

            if 'crime' in check_name and service_model.service_type_id != 29:
                jsn["crime"] = self.json_for_crime_report(payload)
                if jsn["crime"]["is_check_passed"] == False:
                    jsn["crime"]['case_detail'] = self.get_crime_json(payload)
                if 'emp' in check_name:
                    jsn["emp"] = self.json_for_emp_report(payload)
            if 'id_badge' not in check_name:
                jsn["header"] = self.json_for_header(payload)
                jsn["final"] = self.final_result(payload)

            # jsn = {"header": {"client_name": " ABHISHEK PANDEY ", "client_mob": "+919205264013", "report_date": "10-07-2020", "applicant_name": " ABHISHEK PANDEY ", "applicant_phone": "+919205264013", "appicant_address": " 1/863 MAHA DEV NAGAR COLONY SAMNE GHAT LANKA VARANASI - 221005"}, "dl": {"applicant_mobile": "+919205264013", "dob": "01-01-1990", "is_check_passed": true, "color_code": "1", "update_date": "10-07-2020", "applicant_name": "ABHISHEK  PANDEY", "father_name": "RAMESH  CHANDRA PANDEY", "applicant_address": "N 1/863 MAHA DEV NAGAR COLONY SAMNE GHAT LANKA VARANASI 221005", "dl_number": "UP6520130004087", "issue_date": "30-03-2013", "image": "dl_image.jpg", "blood": "", "front_image": "https://s3-external-1.amazonaws.com/media.twiliocdn.com/AC9abf793d66ba45ffd4ed46ca7a7f988f/17ba5eaf922feaafaea5ed6e1a6718bd", "back_image": "https://s3-external-1.amazonaws.com/media.twiliocdn.com/AC9abf793d66ba45ffd4ed46ca7a7f988f/eb53a53e19cc9b483c6f5f56c7e198be", "remark": "10 July 2020"}, "crime": {"applicant_name": " ABHISHEK PANDEY ", "applicant_mobile": "+919205264013", "applicant_address": " 1/863 MAHA DEV NAGAR COLONY SAMNE GHAT LANKA VARANASI - 221005", "dob": "01-01-1990", "father_name": "RAMESH CHANDRA PANDEY", "color_code": "0", "is_check_passed": true, "record_found": " no", "remark": "10 July 2020"}, "emp": {"applicant_name": " ABHISHEK PANDEY ", "applicant_mobile": "+919205264013", "uan_number": "100690260641", "father_name": "RAMESH CHANDRA PANDEY", "update_date": "10-07-2020", "org_detail": [{"org_name": "HELLO VERIFY INDIA PRIVATE LIMITED", "doj": "2020-01-02", "dol": "NA", "address": "B-44 SECTOR-57, NOIDA, UTTAR PRADESH- 201301"}, {"org_name": "MASAMB ELECTRONICS SYSTEM PVT. LTD", "doj": "2016-04-01", "dol": "Not Disclosed", "address": "E-141 SECTOR-63 E-141 SECTOR-63, NOIDA, UTTAR PRADESH- 201307"}], "validation_date": "10-07-2020", "remark": "10 July 2020"}, "final": {"id_type": "DRIVING LICENCE", "id_result": "Green", "uan_result": "Green", "crime_result": "Green", "final_result": "Green", "verify": "GET VERIFIED FOR HIRING", "package_name": "YOUR IDENTITY, CRIMINAL RECORD & EMPLOYMENT"}}
            print("REPORT ENTRY JSON")

            report_obj = Model.report.objects.filter(order__customer_info = session_id).last()
            if report_obj:
                jsn = json.dumps(jsn)
                report_obj.report_json = jsn
                report_obj.save()
            else:
                report_obj = Model.report()
                report_obj.order = order_obj
                jsn = json.dumps(jsn)
                report_obj.report_json = jsn
                report_obj.save()
                
            print("REPORT SAVE JSON")

            return jsn
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json of all the checks and save in database
    '''
    def create_incomplete_report(self,payload):
        try:
            session_id = payload["session_id"]
            cust_model = Model.customer_info.objects.get(session_id = session_id)
            order_obj = Model.order.objects.get(customer_info = session_id)
            service_model = Model.service_detail.objects.filter(customer_type = cust_model.customer_type, service_type_id=cust_model.service_type_id).last()
            check_name = Model.check_types(service_model.check_types).name            
            jsn = {}            
            jsn["header"] = self.json_for_header(payload)
            # get package name
            package_detail = self.get_package_name(session_id)
            jsn["verify"] = package_detail[0]
            jsn["package_name"] = package_detail[1]

            report_obj = Model.report.objects.filter(order__customer_info = session_id).last()
            if report_obj:
                jsn = json.dumps(jsn)
                report_obj.report_json = jsn
                report_obj.save()
            else:
                report_obj = Model.report()
                report_obj.order = order_obj
                jsn = json.dumps(jsn)
                report_obj.report_json = jsn
                report_obj.save()
                
            print("REPORT SAVE JSON")

            return jsn
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    create json for invoice data in report
    '''
    def json_for_invoice(self,payload):
        try:
            print("INSIDE INVOICE REPORT")
            invoice_result = {}
            session_id = payload["session_id"]
            # order_id = payload["order_id"]

            cust_model = Model.customer_info.objects.get(session_id = session_id)

            cust_gst = cust_model.customer_gstin 
            #cust_gst_add = cust_model.address
            cust_gst_add = cust_model.customer_gst_address
            customer_type = cust_model.customer_type
            service_type_id = cust_model.service_type_id

            service_model = Model.service_detail.objects.filter(customer_type = customer_type, service_type_id = service_type_id).last()
            package_name = service_model.service_type_name
            amount = service_model.service_type_price
            final_price = cust_model.final_price
            discount = int(amount - final_price)

            current_date = datetime.datetime.now()
            look_obj = Model.customer_lookup.objects.filter(customer_info = session_id).last()
            if look_obj and (cust_gst_add == None or cust_gst_add.lower() == 'na' or cust_gst_add.lower() == ''):
                invoice_result["client_address"] = look_obj.vendor_name
            else:
                invoice_result["client_address"] = cust_gst_add
            invoice_result["gstin"] = cust_gst
            invoice_result["date"] = current_date.strftime('%d-%m-%Y')
            invoice_result["gst_no"] = '09AAECH4671D1ZM'
            invoice_result["pan_no"] = 'AAECH5671D'
            invoice_result["sac"] = '998521'
            invoice_result["package_name"] = package_name
            invoice_result["number_of_case"] = '1'
            invoice_result["amount"] = amount
            invoice_result["total_amount"] = amount
            invoice_result["discount"] = discount
            invoice_result["net_amount"] = final_price

            # convert number to words
            # from num2words import num2words
            # price_in_words = num2words(cust_model.final_price)
            # invoice_result["amount_in_words"] = price_in_words
            self.invoice = invoice_result

            return self.invoice

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    return invoice json
    '''
    def create_invoice(self,payload):
        try:
            jsn = {}
            jsn["invoice"] = self.json_for_invoice(payload)

            return jsn

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)


    '''
    create json for reminder
    '''
    def json_for_reminder(self,payload):
        try:
            print("INSIDE REMINDER REPORT")
            reminder_result = {}
            session_id = payload["session_id"]
            detail = []
            # get reminder details
            reminder_model = Model.reminder.objects.filter(customer_info = session_id).last()
            if reminder_model:
                dic = {}
                for reminder in range(4):
                    time = reminder_model.updated_at
                    add_4hr = time + datetime.timedelta(hours = 4)
                    dic["time"] = add_4hr
                    dic["msg"] = reminder.message

                    detail.append(dic)

                reminder_result["reminder_detail"] = detail
               
            return reminder_result

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)

    '''
    return cowin report json
    '''
    def cowin_report_json(self,cowin_obj):
        try:
            from fuzzywuzzy import fuzz
            jsn = {}
            res = json.loads(cowin_obj.api_result)
            jsn['user'] = {}
            jsn['cowin'] = {}
            jsn['user']['client'] = cowin_obj.client_name
            jsn['user']['search_id'] = (cowin_obj.check_id).upper()
            jsn['user']['name'] = (cowin_obj.name).title()
            jsn['user']['mobile_no'] = cowin_obj.cowin_mobile_no
            jsn['user']['email_id'] = cowin_obj.email_id if cowin_obj.email_id else 'Not Available'
            jsn['user']['report_date'] = datetime.datetime.now().strftime('%d-%m-%Y')
            
            jsn['cowin']['beneficiary_id'] = 'NA'
            jsn['cowin']['vaccine_name'] = 'NA'
            jsn['cowin']['dose1_center_id'] = 'NA'
            jsn['cowin']['dose1_vaccinated_at'] = 'NA'
            jsn['cowin']['dose1_date'] = 'NA'
        
            jsn['cowin']['dose2_center_id'] = 'NA'
            jsn['cowin']['dose2_vaccinated_at'] = 'NA'
            jsn['cowin']['dose2_date'] = 'NA'
            jsn['cowin']['vaccination_status'] = 'Not Vaccinated'
            cowin_obj.vaccination_status = 'Not Vaccinated'

            if res.get('beneficiaries', None):
                for item in res['beneficiaries']:

                    if fuzz.partial_ratio((cowin_obj.name).lower(), item['name'].lower()) > 80 and \
                        item['birth_year'] == cowin_obj.birth_year:
                        jsn['user']['name'] = item['name']
                        jsn['cowin']['beneficiary_id'] = item['beneficiary_reference_id'] if item['beneficiary_reference_id'] else 'NA'
                        jsn['cowin']['vaccine_name'] = item['vaccine'] if item['vaccine'] else 'NA'
                        jsn['cowin']['vaccination_status'] = item['vaccination_status']
                        jsn['cowin']['dose1_date'] = item['dose1_date'] if item['dose1_date'] else 'NA'
                        jsn['cowin']['dose2_date'] = item['dose2_date'] if item['dose2_date'] else 'NA'
                        cowin_obj.vaccination_status = item['vaccination_status']
                        
                        for i in range(0, len(item['appointments'])):                                               
                            dose = item['appointments'][i]['dose']
                            if "Not Vaccinated" == item['vaccination_status']:
                                break
                            if dose == '1':
                                jsn['cowin']['dose1_center_id'] = item['appointments'][i]['center_id']
                                jsn['cowin']['dose1_vaccinated_at'] = item['appointments'][i]['name']
                            elif dose == '2' and "Vaccinated" == item['vaccination_status']:
                                jsn['cowin']['dose2_center_id'] = item['appointments'][i]['center_id']
                                jsn['cowin']['dose2_vaccinated_at'] = item['appointments'][i]['name']
                        break
            cowin_obj.report_json = json.dumps(jsn)
            cowin_obj.save()
            return jsn

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return str(ex)