from urllib import request
from django.shortcuts import render, HttpResponse
from requests.sessions import session
from hv_whatsapp_api import models as Model
from hv_whatsapp_api.hv_whatsapp_backend import whatsapp_backend_api, processor, report, send_mail as mail
import hv_whatsapp.settings as app_settings
import pdfkit
import json
from datetime import date, datetime, time
import logging, inspect, traceback, secrets, requests
from local_stores.utils import update_stores_for_report_notification, update_cantidate_notification_for_partners

logging.basicConfig(filename="error_log.log")

appbackend = whatsapp_backend_api.Whatsapp_backend()
report_obj = report.Report()

# if app_settings.LOCAL_ENV == False:
#     config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")

if app_settings.LOCAL_ENV == False:
    config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    

# call invoice json and generate invoice and sent to customer
def invoice(request, url_id):
    try:
        order_id = url_id.replace('Invoice_', '')
        dic = {}

        order_obj = Model.order.objects.get(order_id=order_id)
        session_id = order_obj.customer_info.session_id
        payload = {
            'session_id' : session_id,
            'order_id': order_id
        }

        dic = report_obj.create_invoice(payload)
        dic = dic["invoice"]

        return render(request, 'hv_whatsapp_api/hv_invoice.html', dic)
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

def verify_now_invoice(request, url_id):
    try:
        invoice_obj = Model.VerifyNow.objects.get(pk=int(url_id))
        dic = json.loads(invoice_obj.invoice_json)
        return render(request, 'hv_whatsapp_api/verify_now_invoice.html', dic)
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

# generate report and sent to customer
def report(request, sid):
    try:
        rep_obj = Model.report.objects.filter(order__customer_info = sid).last()
        report_data = json.loads(rep_obj.report_json)
        cust_obj = Model.customer_info.objects.get(session_id = sid)
        service_type_id = cust_obj.service_type_id
        customer_type = cust_obj.customer_type
        id_type = cust_obj.id_type
        if id_type == '2' and report_data['dl'] == "'name'":
            return ''
        # print('report data', report_data)
        #testing###########################
        # report_data = {'header': {'client_name': ' ABHISHEK PANDEY ', 'client_mob': '+919205264013', 'report_date': '20-06-2020', 'applicant_name': ' ABHISHEK PANDEY ', 'applicant_phone': '+919205264013', 'appicant_address': ' 1/863 MAHA DEV NAGAR COLONY SAMNE GHAT LANKA VARANASI - 221005'}, 'dl': {'applicant_mobile': '+919205264013', 'dob': '01-01-1990', 'is_check_passed': True, 'color_code': '1', 'update_date': '20-06-2020', 'applicant_name': 'ABHISHEK  PANDEY', 'father_name': 'RAMESH  CHANDRA PANDEY', 'applicant_address': 'N 1/863 MAHA DEV NAGAR COLONY SAMNE GHAT LANKA VARANASI 221005', 'dl_number': 'UP6520130004087', 'issue_date': '30-03-2013', 'image': 'dl_image.jpg', 'blood': '', 'front_image': 'https://s3-external-1.amazonaws.com/media.twiliocdn.com/AC12dc7945cda30019d7389a1310e454bb/17ba5eaf922feaafaea5ed6e1a6718bd', 'back_image': 'https://s3-external-1.amazonaws.com/media.twiliocdn.com/AC12dc7945cda30019d7389a1310e454bb/eb53a53e19cc9b483c6f5f56c7e198be', 'remark': '20 June 2020'}, 'crime': {'applicant_name': ' ABHISHEK PANDEY ', 'applicant_mobile': '+919205264013', 'applicant_address': ' 1/863 MAHA DEV NAGAR COLONY SAMNE GHAT LANKA VARANASI - 221005', 'dob': '01-01-1990', 'father_name': 'RAMESH CHANDRA PANDEY', 'color_code': '0', 'is_check_passed': True, 'record_found': ' no', 'remark': '20 June 2020'}, 'emp': {'applicant_name': ' ABHISHEK PANDEY ', 'applicant_mobile': '+919205264013', 'uan_number': '100690260641', 'father_name': 'RAMESH CHANDRA PANDEY', 'update_date': '20-06-2020', 'org_detail': [{'org_name': 'HELLO VERIFY INDIA PRIVATE LIMITED', 'doj': '2020-01-02', 'dol': 'NA', 'address': 'B-44 SECTOR-57, NOIDA, UTTAR PRADESH- 201301'}, {'org_name': 'MASAMB ELECTRONICS SYSTEM PVT. LTD', 'doj': '2016-04-01', 'dol': '2019-12-31', 'address': 'E-141 SECTOR-63 E-141 SECTOR-63, NOIDA, UTTAR PRADESH- 201307'}], 'validation_date': '20-06-2020', 'remark': '20 June 2020'}, 'final': {'id_type': 'DRIVING LICENCE', 'id_result': 'Green', 'uan_result': 'Green', 'crime_result': 'Green', 'final_result': 'Green', 'verify': 'GET VERIFIED FOR HIRING', 'package_name': 'YOUR IDENTITY, CRIMINAL RECORD & EMPLOYMENT'}}
        # service_type_id = 1
        # id_type = '2'
        # report_data = {'header': {'client_name': 'SAURABH VERMA', 'client_mob': '+919205264013', 'report_date': '20-06-2020', 'applicant_name': 'SAURABH VERMA', 'applicant_phone': '+919205264013', 'appicant_address': '13. BAIDAN TOLA, ETA WAH. ETA WAH, UTTAR PRADESH-206001'}, 'adhaar': {'applicant_name': 'SAURABH VERMA', 'applicant_mobile': '+919205264013', 'applicant_address': '13. BAIDAN TOLA, ETA WAH. ETA WAH, UTTAR PRADESH-206001', 'adhaar_number': '2443 4056 0639', 'dob': '29-05-1990', 'father_name': 'SWARJYA SINGH VERMA', 'is_check_passed': True, 'update_date': '20-06-2020', 'color_code': '1', 'number_valid': 'Green', 'age_valid': 'Green', 'gender_valid': 'Green', 'state_valid': 'Green', 'uid_data': '2443 4056 0639', 'age_data': '30-40', 'mobile_data': 'xxxxxxx013', 'state_data': 'UTTAR PRADESH', 'gender_data': 'MALE', 'pin_data': '206001', 'front_image': 'https://s3-external-1.amazonaws.com/media.twiliocdn.com/AC12dc7945cda30019d7389a1310e454bb/a58135decc2cc69da2e3975159656d25', 'back_image': 'https://s3-external-1.amazonaws.com/media.twiliocdn.com/AC12dc7945cda30019d7389a1310e454bb/4d353e6d54ec8d2dc58da19cace702a9', 'remark': '20 June 2020'}, 'crime': {'applicant_name': 'SAURABH VERMA', 'applicant_mobile': '+919205264013', 'applicant_address': '13. BAIDAN TOLA, ETA WAH. ETA WAH, UTTAR PRADESH-206001', 'dob': '29-05-1990', 'father_name': 'SWARJYA SINGH VERMA', 'color_code': '0', 'is_check_passed': True, 'record_found': ' no', 'remark': '20 June 2020'}, 'emp': {'applicant_name': 'SAURABH VERMA', 'applicant_mobile': '+919205264013', 'uan_number': '100604263168', 'father_name': 'SWARJYA SINGH VERMA', 'update_date': '20-06-2020', 'org_detail': [{'org_name': 'HELLO VERIFY INDIA PRIVATE LIMITED', 'doj': '2020-02-10', 'dol': 'NA', 'address': 'B-44 SECTOR-57, NOIDA, UTTAR PRADESH- 201301'}, {'org_name': 'CPA  GLOBAL SUPPORT SERVICES INDIA PRIVATE LIMITED', 'doj': '2015-08-24', 'dol': '2020-01-15', 'address': '2ND FLOOR,1/3,SRI GANGARAM HOSPITAL 2ND FLOOR,1/3,SRI GANGARAM HOSPITAL, NEW DELHI, DELHI- 110060'}], 'validation_date': '20-06-2020', 'remark': '20 June 2020'}, 'final': {'id_type': 'AADHAAR CARD', 'id_result': 'Green', 'uan_result': 'Green', 'crime_result': 'Green', 'final_result': 'Green', 'verify': 'GET VERIFIED FOR HIRING', 'package_name': 'YOUR IDENTITY, CRIMINAL RECORD & EMPLOYMENT'}}
        # service_type_id = 2
        # id_type = '1'
        #############################
        # get checks detail from service type
        service_model = Model.service_detail.objects.filter(customer_type = customer_type, service_type_id=service_type_id).last()
        check_name = Model.check_types(service_model.check_types).name
        if id_type == '1':
            if "id_crime_check" == check_name and service_model.service_type_id==29:
                html_template = 'hv_whatsapp_api/reports/ssl_aadhaar_annexure.html' 
            elif "id_crime_check" == check_name:
                html_template = 'hv_whatsapp_api/reports/aadhaar_annexure_new.html'
            elif "id_crime_emp_check" == check_name:
                html_template = 'hv_whatsapp_api/reports/aadhaar_emp_annexure.html'
            elif "id_check" == check_name:
                html_template = 'hv_whatsapp_api/reports/kyi_aadhaar_annexure.html'
            elif "id_badge" == check_name:
                html_template = 'hv_whatsapp_api/reports/adhaar_badge.html'
            elif "kyc_check" == check_name and customer_type == '1':
                html_template = 'hv_whatsapp_api/reports/kyc_aadhaar_myself.html'
            elif "kyc_check" == check_name and customer_type == '2':
                html_template = 'hv_whatsapp_api/reports/kyc_aadhaar_someone.html'
        else:
            if "id_crime_check" == check_name and service_model.service_type_id==29:
                html_template = 'hv_whatsapp_api/reports/ssl_dl_annexure.html'
            elif "id_crime_check" == check_name:
                html_template = 'hv_whatsapp_api/reports/dl_annexure.html'
            elif "id_crime_emp_check" == check_name:
                html_template = 'hv_whatsapp_api/reports/dl_emp_annexure.html'
            elif "id_check" == check_name:
                html_template = 'hv_whatsapp_api/reports/kyi_dl_annexure.html'
            elif "id_badge" == check_name:
                html_template = 'hv_whatsapp_api/reports/dl_badge.html'
            elif "kyc_check" == check_name and customer_type == '1':
                html_template = 'hv_whatsapp_api/reports/kyc_dl_myself.html'
            elif "kyc_check" == check_name and customer_type == '2':
                html_template = 'hv_whatsapp_api/reports/kyc_dl_someone.html'

        return render(request, html_template, {'jsn': report_data})
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

# generate report and sent to customer
def incomplete_report(request, sid):
    try:
        rep_obj = Model.report.objects.filter(order__customer_info = sid).last()
        report_data = json.loads(rep_obj.report_json)
        cust_obj = Model.customer_info.objects.get(session_id = sid)
        service_type_id = cust_obj.service_type_id
        customer_type = cust_obj.customer_type
        
        # get checks detail from service type
        service_model = Model.service_detail.objects.filter(customer_type = customer_type, service_type_id=service_type_id).last()
        check_name = Model.check_types(service_model.check_types).name
        if "emp" in check_name:
            html_template = 'hv_whatsapp_api/reports/no_doc_emp.html'
        elif "crime" in check_name:
            html_template = 'hv_whatsapp_api/reports/no_doc.html'
        else:
            html_template = 'hv_whatsapp_api/reports/no_doc_id.html'

        return render(request, html_template, {'jsn': report_data})
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

def is_session_expired(db_time):
    now = datetime.now()
    timediff = now - db_time
    time_diff = timediff.total_seconds()//3600
    if time_diff > 24:
        return True
    return False

# generate report and sent to customer
# def generate_report(request):
def generate_report(mobile_no, session_id):
    try:    
        ########testing##########
        # session_id = '596b42ac8bdd4db4ab29d5b74f5ab0fc' # adhaar
        # session_id = '58236a9908d64a19b703107feb39f85c' # dl
        # session_id = 41 # dl
        ##########testing#############
        print("INSIDE GENERATE REPORT")
        order_obj = Model.order.objects.get(customer_info = session_id)
        order_id = order_obj.order_id
        payload = {'session_id': session_id, 'order_id': order_id}
        crime_obj = Model.criminal_result.objects.filter(order = order_id).last()
        if crime_obj and crime_obj.manual_color_code == '3': #manual uncommenting
            return ''
        jsn = report_obj.create_report(payload)
        
        if session_id == 4873:
            save_dir = '/datadrive/media/ihv/Report_E8AA414B.pdf'
        elif session_id == 11640:
            save_dir = '/datadrive/media/ihv/Report_159EF711632.pdf'
        else:
            report_name = 'Report_'+order_id+'.pdf'
            save_dir = f'/datadrive/media/ihv/{report_name}'
            report_url = f'https://checkapi.helloverify.com/media/ihv/{report_name}'
            
        url = 'https://checkapi.helloverify.com/report/report/sid'.replace('sid', str(session_id))
        if app_settings.LOCAL_ENV == False:
            pdfkit.from_url(url, save_dir,configuration = config)
        else:
            pdfkit.from_url(url, save_dir)
        #for demo case
        if session_id in [4873,11640]:
            return True
        report_check = Model.report_check.objects.filter(order = order_id).last()
        report_check.report_status = '1' #generated
        report_check.save()
        
        crime_obj = Model.criminal_result.objects.filter(order__order_id = order_id).last()
        order_obj.auto_or_manual = ('Auto' if not crime_obj or crime_obj.manual_color_code == '0' else 'Manual')        
        jsn = json.loads(jsn)
        if crime_obj:
            order_obj.final_status = jsn['final']['final_result']
        else: #for id badge
            order_obj.final_status = "Green"
        
        order_obj.report_url = report_url
        order_obj.save()

        mail_obj = mail.Send_Email()
        subject = 'Report generated for Order_ID - ' + order_id
        content = 'Report has generated, please review and send.<br/><br/>'+report_url
        mail_obj.process(subject, content)
        return True
        ##########testing#############
        # rep_obj = Model.report.objects.filter(session_id = session_id).last()
        # report_data = json.loads(rep_obj.report_json)
        # return render(request, 'hv_whatsapp_api/reports/adhaar_badge.html', {'jsn': report_data})
        ##########testing#############
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

# generate report and sent to customer
# def generate_report(request):
def generate_incomplete_report(mobile_no, session_id):
    try:    
        print("INSIDE GENERATE REPORT")
        order_obj = Model.order.objects.get(customer_info = session_id)
        order_id = order_obj.order_id
        payload = {'session_id': session_id, 'order_id': order_id}

        jsn = report_obj.create_incomplete_report(payload)
        report_name = 'Report_'+order_id
        save_dir = f'/datadrive/media/ihv/{report_name}.pdf'
        report_url = f'https://checkapi.helloverify.com/media/ihv/{report_name}.pdf'
        url = 'https://checkapi.helloverify.com/report/incomplete_report/sid'.replace('sid', str(session_id))
        pdfkit.from_url(url, save_dir,configuration = config)
        
        order_obj.auto_or_manual = 'Incomplete report'
        order_obj.final_status = 'Incomplete'
        order_obj.report_url = report_url
        order_obj.save()

        mail_obj = mail.Send_Email()
        subject = 'Incomplete report generated for Order_ID - ' + order_id
        content = 'Report has generated, please review and send.<br/><br/>'+report_url
        mail_obj.process(subject, content)
        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

def cowin_report(request, sid):
    try:
        html_template = 'hv_whatsapp_api/reports/cowin_report.html'
        cowin_obj = Model.CowinData.objects.get(check_id = sid)
        report_json = json.loads(cowin_obj.report_json)
        return render(request, html_template, {'jsn':report_json})
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

def generate_cowin_report(cowin_obj):
    try:
        from hv_whatsapp_api.hv_whatsapp_backend import report
        report_obj = report.Report()
        report_obj.cowin_report_json(cowin_obj) 
        
        report_name = 'Report_'+cowin_obj.check_id
        if app_settings.LOCAL_ENV == False:
            url = 'https://checkapi.helloverify.com/report/cowin_report/sid'.replace('sid', str(cowin_obj.check_id))
        else:
            url = 'http://localhost:8000/report/cowin_report/sid'.replace('sid', str(cowin_obj.check_id))
        save_dir = f'/datadrive/media/cowin/{report_name}.pdf'
        # save_dir = f'hv_whatsapp_api/static/{report_name}.pdf'
        if app_settings.LOCAL_ENV == False:
            pdfkit.from_url(url, save_dir,configuration = config)
        else:
            pdfkit.from_url(url, save_dir)
        report_url = f'https://checkapi.helloverify.com/media/cowin/{report_name}.pdf'
        mail_obj = mail.Send_Email()
        subject = 'Cowin report generated for Check_ID - ' + cowin_obj.check_id
        content = 'Report has generated, please review and send.<br/><br/>'+report_url
        mail_obj.process(subject, content)
        return report_url
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

def send_cowin_report(cowin_obj):
    try:
        if 'cowin' in cowin_obj.check_id.lower():
            report_name = 'Report_'+cowin_obj.check_id
            report_url = f'https://checkapi.helloverify.com/media/cowin/{report_name}.pdf'
            pay_obj = processor.DB_Processor()
            pay_obj.sent_reminder(cowin_obj.whatsapp_mobile_no, report_name, report_url)
        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False
# delete image of customer for DL after report generate
def delete_local_img(session_id):
    try:

        file_path = "static/img/{}.jpg".format(session_id)

        import os
        if os.path.exists(file_path):
            os.remove(file_path)
            print("Image deleted successfully")
        else:
            print("Image does not exist")

        return True

    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

def encrypt_report(report_url, name, mobile_no):
    try:
        from PyPDF2 import PdfWriter, PdfWriter
        out = PdfWriter()
        file_path = "/datadrive" + report_url.split('.com')[-1]
        file = PdfWriter(file_path)
        # num = file.numPages
        # num = file.getNumPages
        # num = file.getNumPages()
        num = len(file.pages)

        for idx in range(num):
            page = file.getPage(idx)
            out.addPage(page)
        
        password = name.lower().replace(' ', '').replace('.', '')[:4] + mobile_no[-4:]

        out.encrypt(password)

        with open(file_path, "wb") as f:
            out.write(f)

    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

# Sending Report to Customer (Here we can protect the report by password and password will be (starting 4 digit of name and last 4 digit of contact number of client) like sono7010)
def send_report(mobile_no, session_id, report_obj):
    try:
        order_id = report_obj.order_id
        report_url = report_obj.order.report_url
        
        report_obj.report_status = '2'
        report_obj.save()

        # encrypt_report(report_url, report_obj.order.name, mobile_no)
        
        pay_obj = processor.DB_Processor()
        if is_session_expired(report_obj.order.payment_recieved_date):
            ques_obj = Model.question_master.objects.get(question_id=70)
            ques_text = ques_obj.question_desc_eng
            pay_obj.sent_reminder(mobile_no, ques_text, report_url)
        else:
            pay_obj.sent_reminder(mobile_no, 'Report', report_url)

        delete_local_img(session_id)

        # update report sent time in admin order model
        order_obj = Model.order.objects.filter(order_id = order_id).last()
        order_obj.report_sent_time = datetime.now()
        order_obj.save()
        
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

############ testing start #############
def send_mesg_forcefully(request):
    try:
        data = json.loads(request.body)
        from twilio.rest import Client
        account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
        auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
        client = Client(account_sid, auth_token)

        message = client.messages \
            .create(
                media_url=[data.get('url', None)],
                from_='whatsapp:+14157924931',
                body=data['mesg'],
                to='whatsapp:'+data['mobile_no']
            )
        return HttpResponse('Message sent successfully')
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return HttpResponse('Message failed to sent')

############ testing start #############
def index1(request, sid):
    try:
        # import requests, time, os
        # path = '/datadrive/media/edu/' + item.unique_id
        # os.mkdir(path)
        # r = requests.get("https://s3-external-1.amazonaws.com/media.twiliocdn.com/ACdca0e8e83c002ca63cd670ee736fccd6/e041a3c16022145bf54e0e80c6d60ed1", stream=True)
        # ext = r.headers['content-type'].split('/')[-1] # converts response headers mime type to an extension (may not work with everything)

        # file_name = path + '/' + time.time() + ext
        # with open("%s.%s" % (time.time(), ext), 'wb') as f: # open the file to write as binary - replace 'wb' with 'w' for text files
        #     for chunk in r.iter_content(1024): # iterate on stream using 1KB packets
        #         f.write(chunk) # write the file
        # return HttpResponse('thanks')
        # import requests
        # image_url = "https://s3-external-1.amazonaws.com/media.twiliocdn.com/ACdca0e8e83c002ca63cd670ee736fccd6/cd9a0f0bb20b6161fc0dfba3710e8ac5"
        
        # # URL of the image to be downloaded is defined as image_url
        # r = requests.get(image_url) # create HTTP response object
        # print(r)
        # subject = "Cowin verification email"
        # content = '''<html xmlns="http://www.w3.org/1999/xhtml" ><head><title>Candidate Details</title><style>body {font-family:Verdana; font-size:10px;}a{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#105496;text-decoration:none;background-color:Transparent;float:left;}.a:hover{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#000000;text-decoration:none;background-color:Transparent;float:left;}.a:active{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#000000;text-decoration:none;background-color:Transparent;float:left;}</style></head><body><table width="600" border="1" cellpadding="10" cellspacing="1" bordercolor="#666666"><tr><td align="Center" height="50" width="485"><img alt="helloverify" src="https://www.helloverify.com/assets/images/logo.PNG" /><br/>(This is an auto generated email, kindly do not revert)</td></tr><tr><td><br/><br/>'''+\
        # "Please click on below link and enter the automatically typed text to initiate the process.<br/><br/>"\
        # "https://api.whatsapp.com/send?phone=14157924931&text=ABC123<br/>"\
        # '''<br/><br/>Regards<br/>Helloverify Team<br/></td></tr><tr><td style='font-size:11px;font-family:Arial,Helvetica,sans-serif;text-align:left;color:#454545;line-height:20px;text-decoration:none;vertical-align:middle;line-height:18px'>In case of any further queries kindly write to us at below email id. We will be happy to help. <br/>hellov@helloverify.com</td></tr></table></body></html>'''
        # content = '''<html xmlns="http://www.w3.org/1999/xhtml" ><head><title>Candidate Details</title><style>body {font-family:Verdana; font-size:10px;}a{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#105496;text-decoration:none;background-color:Transparent;float:left;}.a:hover{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#000000;text-decoration:none;background-color:Transparent;float:left;}.a:active{width:400px;margin-left:15px;float:left;font-family:Arial;text-align:left;font-size:12px;color:#000000;text-decoration:none;background-color:Transparent;float:left; .pill-btn{display: inline-block;box-sizing: border-box; height: 50px;background:green;padding: 0px 30px;border-radius: 999em;text-decoration: none;color: #fff;font-size: 16px;vertical-align: bottom;white-space: nowrap;border: 3px solid green;font-family: lato;letter-spacing: 2px;transition: .15s background-color, .15s border-color, .15s color, .15s fill;font-weight: 600;}}</style></head><body><table width="600" border="1" cellpadding="10" cellspacing="1" bordercolor="#666666"><tr><td align="Center" height="50" width="485"><img alt="helloverify" src="https://www.helloverify.com/assets/images/logo.PNG" /><br/>(This is an auto generated email, kindly do not revert)</td></tr><tr><td><br/><br/>'''+\
        # "Please click on below link and enter the automatically typed text to initiate the process.<br/><br/> <div style='display: grid;place-items: center;'><button type='submit' class='pill-btn' style='position: relative;text-align: center;'>Click here</button></div>"\
        # "https://api.whatsapp.com/send?phone=14157924931&text=ABC123<br/>"\
        # '''<br/><br/>Regards<br/>Helloverify Team<br/></td></tr><tr><td style='font-size:11px;font-family:Arial,Helvetica,sans-serif;text-align:left;color:#454545;line-height:20px;text-decoration:none;vertical-align:middle;line-height:18px'>In case of any further queries kindly write to us at below email id. We will be happy to help. <br/>hellov@helloverify.com</td></tr></table></body></html>'''
        # mail_process = mail.Send_Email()
        # mail_process.process(subject,content)  
        # mail_obj = mail.Send_Email()
        # subject = 'saurabh testing'
        # content = 'saurabh testing'
        # mail_obj.process(subject, content)
        # rep_obj = Model.report.objects.get(order__order_id = '5415ABE3') #dl
        # rep_obj = Model.report.objects.get(order__order_id = '8DE4FB29') #aadhaar
        # report_data = json.loads(rep_obj.report_json)
        # cowin_obj = Model.CowinData.objects.get(check_id=1)
        # report_json = json.loads(cowin_obj.report_json)
        # # a = 'https://s3-external-1.amazonaws.com/media.twiliocdn.com/ACdca0e8e83c002ca63cd670ee736fccd6/399bb8f4bafacfd8bd106089cfad451f'
        # print('index1')
        # # payload = {
        
        # # 'candidate_name': 'Saurabh Verma', 
        # # 'address': 'x-17 sec 12 noida', 
        # # 'proof_doc_type': 'aadhaar',
        # # 'color': 'RED',
        # # 'result': 'RED',
        # # 'ownership_status': 'Rental',
        # # 'type_of_address': 'Current Address',
        # # 'period_of_stay_from': '2020',
        # # 'period_of_stay_to': '2021',
        # # 'proof_doc_type': 'dl',
        # # 'capturedMAPImagedoc': a,
        # # 'proofdocback': a,
        # # 'proofdocfront': a,
        # # 'signaturedoc': a,
        # # 'selfie': a,
        # # 'gatedoc': a,
        # # }
        jsn = {"user": {"client": "Demo", "search_id": "ABC123", "name": "SAURABH VERMA", "mobile_no": "+919205264013", "email_id": "saurabh.verma@helloverify.com", "report_date": "26-10-2021"}, "cowin": {"beneficiary_id": "73901858836120", "vaccine_name": "COVISHIELD", "dose1_center_id": 748901, "dose1_vaccinated_at": "METRO HOSPITALS", "dose1_date": "24-06-2021", "dose2_center_id": 875715, "dose2_vaccinated_at": "Radha Soami Satsung Beas Kosh.", "dose2_date": "17-09-2021", "vaccination_status": "Not Vaccinated"}}
        return render(request, 'hv_whatsapp_api/reports/cowin_report.html', {'jsn': jsn})
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False


from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from feedback.views import send_feedback_link

@receiver(post_save, sender=Model.report_check)
def send_mail(sender, instance, *args, **kwargs):
    try:
        mail_process = mail.Send_Email()
        session_id = instance.order.customer_info.session_id
        
        if instance.send_report and instance.report_status == '1':            
            cust_obj = Model.customer_info.objects.get(session_id = session_id)
            if instance.send_review_mail:
                subject = 'Hellov report sent successfully'
                content = "Hello Sir,<br><br>Report Sent successfully. PFA report for your reference.<br><br>Thanks,<br>HelloV Team"
                filename = '/datadrive'+instance.order.report_url.split('.com')[-1]
                mail_process.process(subject,content, filename)
            if cust_obj.customer_type == '1':
                mobile_no = cust_obj.mobile_no
            elif cust_obj.customer_type == '3':
                lookup_obj = Model.customer_lookup.objects.filter(customer_info = session_id).last()
                mobile_no = lookup_obj.vendor_mobile
            update_stores_for_report_notification(session_id)
            update_cantidate_notification_for_partners(session_id)    
            send_report(mobile_no, session_id, instance)
            try:
                send_feedback_link(instance)
            except Exception as ex:
                pass    
        
        # elif instance.send_review_mail and instance.report_status == '1':
        # elif instance.send_mail_for_manual_check and instance.report_status == '0':
        #     ocr_obj = Model.ocr_response.objects.filter(customer_info = session_id).last()                                
        #     subject = 'Manual Crime Check'
        #     content = '''Please do manual crime check within 5 hours for order id: %s <br><br>
        #     http://52.66.35.239:8007/Account/Login<br><br>
        #     Please check below IDs for your reference:<br><br>''' % order_id
        #     content = content + str(ocr_obj.front_image_url)+'<br><br>'+str(ocr_obj.back_image_url)
        #     mail_process.process(subject,content)

        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

@receiver(post_save, sender=Model.order)
def customer_consent(sender, instance, created, *args, **kwargs):
    try:
        if created:            
            constent_obj = Model.consent()
            constent_obj.order = instance
            constent_obj.name = instance.customer_info.name
            constent_obj.mobile_number = instance.customer_info.mobile_no
            constent_obj.save()           

            from promotional_marketing.models import PromotionalMessageTracker
            
            promo_obj = PromotionalMessageTracker.objects.filter(mobile_no=instance.customer_info.mobile_no).last()
            if promo_obj:
                promo_obj.is_purchased=True
                promo_obj.last_purchase_date=datetime.now()
                promo_obj.save()

        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

@receiver(pre_save, sender=Model.order)
def send_incomplete_report(sender, instance, *args, **kwargs):
    try:
        order_obj = sender.objects.filter(order_id = instance.order_id).last()
        if order_obj and order_obj.send_incomplete_report == False and instance.send_incomplete_report == True:
            report_url = order_obj.report_url
            instance.report_sent_time = datetime.now()
            encrypt_report(report_url, order_obj.name, order_obj.mobile_no)
            
            pay_obj = processor.DB_Processor()
            if is_session_expired(order_obj.payment_recieved_date):
                ques_obj = Model.question_master.objects.get(question_id=70)
                ques_text = ques_obj.question_desc_eng
                pay_obj.sent_reminder(order_obj.mobile_no, ques_text, report_url)
            else:
                pay_obj.sent_reminder(order_obj.mobile_no, 'Report', report_url)
        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

# Send reminder to particular whatsapp number
def sent_reminder(mobile, mesg, url=None):
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

@receiver(post_save, sender=Model.CowinData)
def cowin_initiation(sender, instance, created, *args, **kwargs):
    try:
        if created and 'cowin' not in (str(instance.check_id)).lower():
            ques_obj = Model.question_master.objects.get(question_id = 2001)
            final_ques = ques_obj.question_desc_eng.format(name=instance.name.title(), client_name=instance.client_name, whatsapp_mobile_no=instance.whatsapp_mobile_no[3:])
            sent_reminder(instance.whatsapp_mobile_no, final_ques)
        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

@receiver(post_save, sender=Model.customer_info)
@receiver(post_save, sender=Model.ocr_response)
@receiver(post_save, sender=Model.url_expiry)
def adminmodel(sender, instance, *args, **kwargs):
    try:
        if sender.__name__ == 'customer_info' and instance.customer_type == '3':
            return True
        if sender.__name__ == 'customer_info':
            session_id = instance.session_id
        else:
            session_id = instance.customer_info.session_id
        admin_obj = Model.AdminIncompleteTransactionModel.objects.filter(customer_info = session_id).last()
        if not admin_obj and sender.__name__ == 'customer_info':
            admin_obj = Model.AdminIncompleteTransactionModel()
            admin_obj.customer_info = instance
            admin_obj.mobile_no = instance.mobile_no
            if instance.service_type_id < 20:
                    admin_obj.starts_with = 'HELLOV'
            else:
                admin_obj.starts_with = 'HELLO REDEEM'
        elif admin_obj and sender.__name__ == 'url_expiry' and not instance.expired:
            admin_obj.payment_link_status = 'Sent'
        elif admin_obj and sender.__name__ == 'ocr_response':
            admin_obj.id_uploaded = Model.id_type(instance.id_type).name
        elif admin_obj and sender.__name__ == 'customer_info':
            if admin_obj.language_selected == '--':
                admin_obj.language_selected = ('English' if int(instance.language_type) == 1 else 'Hindi')
            elif admin_obj.customer_type == '--' and admin_obj.starts_with != 'HELLO REDEEM':
                admin_obj.customer_type = ('Myself' if int(instance.customer_type) == 1 else 'Someone Else')
            elif instance.promo_applied != '--':
                admin_obj.promo_applied = instance.promo_applied
            elif instance.service_type_id not in [0, 20]:
                service_obj = Model.service_detail.objects.filter(service_type_id = instance.service_type_id, customer_type = instance.customer_type).last()
                admin_obj.package_name = service_obj.service_type_name
        if admin_obj:
            admin_obj.save()
        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False


# cache clear when any update in question_master, myself, someone
@receiver(post_save, sender=Model.question_master)
@receiver(post_save, sender=Model.communication_myself)
@receiver(post_save, sender=Model.communication_someoneelse)
def update_cache(sender, instance, *args, **kwargs):
    try:
        from django.core.cache import cache

        cache.clear()
        
        from django.db.models import Q
        ques_obj = Model.question_master.objects.filter(Q(question_id__gte=3000) & Q(question_id__lte=3005))
        cache.set('verifynow_3000', ques_obj[0].question_desc_eng, None)
        cache.set('verifynow_3001', ques_obj[1].question_desc_eng, None)
        cache.set('verifynow_3002', ques_obj[2].question_desc_eng, None)
        cache.set('verifynow_3003', ques_obj[3].question_desc_eng, None)
        cache.set('verifynow_3004', ques_obj[4].question_desc_eng, None)
        cache.set('verifynow_3005', ques_obj[5].question_desc_eng, None)

        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return str(ex)

#whatsapp ids databackup
def ids_data_backup():
    batch = Model.ocr_response.objects.all()
    if batch:
        for item in batch:
            try:
                import requests, time, os
                sid = str(item.customer_info.session_id)
                path = '/datadrive/media/ids/' + sid
                import os

                if item.front_image_url is None and item.back_image_url is None:
                    continue
                
                if not os.path.exists(path):
                    os.mkdir(path)
                else:
                    continue
                
                doc_url_list = []
                if item.front_image_url and 'twilio' in item.front_image_url:
                    doc_url_list.append(item.front_image_url)
                if item.back_image_url and 'twilio' in item.back_image_url:
                    doc_url_list.append(item.back_image_url)
                
                if not doc_url_list:
                    continue
                
                for url in doc_url_list:
                    try:
                        r = requests.get(url, stream=True)
                        ext = r.headers['content-type'].split('/')[-1] # converts response headers mime type to an extension (may not work with everything)

                        file_name = path + '/' + str(time.time())
                        with open("%s.%s" % (file_name, ext), 'wb') as f: # open the file to write as binary - replace 'wb' with 'w' for text files
                            for chunk in r.iter_content(1024): # iterate on stream using 1KB packets
                                f.write(chunk) # write the file
                    except Exception as ex:
                        print('unable to download files')
                
                import glob
                new_doc_url_list = glob.glob(path+"/*")
                new_doc_url_list = [item.replace('/datadrive','') for item in new_doc_url_list]
                if item.front_image_url and 'twilio' in item.front_image_url:
                    item.front_image_url = new_doc_url_list.pop(0)
                if item.back_image_url and 'twilio' in item.back_image_url:
                    item.back_image_url = new_doc_url_list.pop(0)

                item.save()
                print('success')
            except Exception as ex:
                print('Failed')
                continue

def edu_data_backup():
    batch = Model.EducationData.objects.filter(hide_record=False)
    if batch:
        for item in batch:
            try:
                import requests, time, os
                path = '/datadrive/media/edu/' + item.unique_id
                import os
                    
                if not os.path.exists(path):
                    os.mkdir(path)
                else:
                    continue

                if item.tenth_url is None and item.twelveth_url is None and item.extra_urls == '-':
                    continue

                doc_url_list = []
                if item.tenth_url:
                    doc_url_list.append(item.tenth_url)
                if item.twelveth_url:
                    doc_url_list.append(item.twelveth_url)
                if item.extra_urls != '-':
                    doc_url_list = doc_url_list + item.extra_urls.split(',')
                for url in doc_url_list:
                    try:
                        r = requests.get(url, stream=True)
                        ext = r.headers['content-type'].split('/')[-1] # converts response headers mime type to an extension (may not work with everything)

                        file_name = path + '/' + str(time.time())
                        with open("%s.%s" % (file_name, ext), 'wb') as f: # open the file to write as binary - replace 'wb' with 'w' for text files
                            for chunk in r.iter_content(1024): # iterate on stream using 1KB packets
                                f.write(chunk) # write the file
                    except Exception as ex:
                        print('unable to download files')
                
                import glob
                new_doc_url_list = glob.glob(path+"/*")
                new_doc_url_list = [item.replace('/datadrive','') for item in new_doc_url_list]
                if item.tenth_url and 'twilio' in item.tenth_url:
                    item.tenth_url = new_doc_url_list.pop(0)
                if item.twelveth_url and 'twilio' in item.twelveth_url:
                    item.twelveth_url = new_doc_url_list.pop(0)
                if item.extra_urls != '-' and 'twilio' in item.extra_urls:
                    item.extra_urls = ','.join(new_doc_url_list)
                item.save()
                print('success')
            except Exception as ex:
                print('Failed')
                continue

@receiver(post_save, sender=Model.NobrokerOrder)
def nobroker_customer_invite(sender, instance, created, *args, **kwargs):
    try:
        if created:
            email_template = Model.EmailTemplate.objects.get(template_name = "nobroker_template").email_html
            question_text = Model.question_master.objects.get(question_id = 2007).question_desc_eng

            redemption_pin = appbackend.get_redemption_pin(int(instance.package), instance.mobile_no)
            if not redemption_pin:
                raise ValueError('No coupon code found - Admin please review the issue')

            # Sending whatsapp message
            whatsapp_message = question_text.format(applicant_name=instance.applicant_name.title(), redemption_pin=redemption_pin)
            sent_reminder(instance.mobile_no, whatsapp_message)
            
            # Sending email
            service_type_name = Model.nobroker_package_name(instance.package).name
            if '_or_' in service_type_name:
                service_type_name = service_type_name.replace('_or_', '/')
            service_type_name = service_type_name.replace('_', ' ')
            
            subject = 'Welcome to Helloverify - Order ID: ' + instance.order_id.upper()
            content = email_template.format(applicant_name=instance.applicant_name.title(), service_type_name=service_type_name, \
                redemption_pin=redemption_pin)
            mail_obj = mail.Send_Email()
            mail_obj.process(subject, content, '', instance.email_id)

            subject = 'NoBroker - Order Received'
            email_template = Model.EmailTemplate.objects.get(template_name = "nobroker_order").email_html
            content = email_template.format(applicant_name=instance.applicant_name.title(), service_type_name=service_type_name, \
                order_id=instance.order_id.upper())
            mail_obj = mail.Send_Email()
            mail_obj.process(subject, content, '', instance.email_id)

            # Sending SMS
            # sms_template = Model.EmailTemplate.objects.get(template_name = "nobroker_sms").email_html
            
            # sms_content = sms_template.format(applicant_name=instance.applicant_name.title(), redemption_pin=redemption_pin)
            # url = app_settings.EXTERNAL_API['SMS_URL'].format(mobile_no=instance.mobile_no[3:], sms_content=sms_content)+"&entityid=1001629542890983159&tempid=1007155458403530924"
            # requests.get(url)
        return True
    except Exception as ex:
        traceback.print_exc()
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

def create_razorpay_link(mobile_no, service_type_name, service_type_price):
    import razorpay, datetime
    try:
        client = razorpay.Client(auth=(app_settings.RAZORPAY_KEYS['RAZORKEY'], app_settings.RAZORPAY_KEYS['RAZORSECRET']))
        current_time = datetime.datetime.now(datetime.timezone.utc)
        unix_timestamp = current_time.timestamp()
        unix_timestamp_plus_30_min = int(unix_timestamp + (30 * 60))
        # service_type_price = service_type_price//2

        reg_obj = Model.customer_register.objects.filter(mobile_no=mobile_no).last()
        if reg_obj and reg_obj.mobile_verified:
            service_type_price = 1

        res = client.payment_link.create({
        "amount": service_type_price * 100,
        "currency": "INR",
        "description": service_type_name,
        "expire_by": unix_timestamp_plus_30_min,
        "customer": {
            "name": "",
            "email": "",
            "contact": mobile_no[3:]
        },
        "notify": {
            "sms": True,
            "email": True
        },
        "reminder_enable": True,
        "notes": {
            "link_name": "hellov_order"
        },
        "callback_url": "https://checkapi.helloverify.com/api/whatsapp/razorpay_callback_url/",
        "callback_method": "get",
        # "options": {
        #     "order": {
        #     "offers": [
        #         "offer_JR2irM7NI8n2vg",
        #         "offer_JR33Y8igniM50j",
        #         "offer_JRDAWfb3Ak1Fyp",
        #         "offer_JRDGJEE7nmcXz0"
        #     ]
        #     }
        # }
        })
        return res
    except Exception as ex:
        traceback.print_exc()
        logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

@receiver(pre_save, sender=Model.VerifyNow)
def verify_now_service(sender, instance, *args, **kwargs):
    try:
        sender_obj = sender.objects.filter(mobile_no= instance.mobile_no, is_session_expired=False).last()
        if sender_obj and sender_obj.service_type_id != instance.service_type_id:
           
            instance.is_session_expired = True
            service_detail_obj = Model.service_detail.objects.filter\
                (service_type_id=instance.service_type_id).last()

            instance.service_detail = service_detail_obj

            res = create_razorpay_link(instance.mobile_no, \
                service_detail_obj.service_type_name.split(' - ')[0], \
                    int(service_detail_obj.service_type_price))

            instance.short_url = res['short_url']
            instance.razorpay_payment_link_id = res['id']
            
        else:
            pass
    except Exception as ex:
        traceback.print_exc()
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return False

def id_check_scheduler(request):
    print('id_check_scheduler1-->' + str(datetime.now()))
    try:
        from hv_whatsapp_api.hv_whatsapp_backend import views as apicall
        # find batch for id_check_status = False
        batch = Model.report_check.objects.filter(id_check_status = False)

        for item in batch:                
            order_id = item.order.order_id
            print('id_check ' + str(datetime.now()) + ' order_id ' + order_id)
            session_id = item.order.customer_info.session_id
            id_type = item.order.customer_info.id_type
            payload = {"session_id": session_id}
            
            api_obj = Model.api_hit_count.objects.get(order = order_id)
            call_id_api = apicall.Views()
            if id_type == '1':
                if api_obj.anti_captcha >= 6:
                    continue
                call_id_api.get_adhaar_results(payload) 
            elif id_type == '2':
                if api_obj.dl_api >= 1:
                    continue
                call_id_api.get_dl_results(payload)   
                
        return True
    except Exception as ex:
        print(traceback.print_exc())
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
        return str(ex)

def generate_unique_codes(request,rang,service_id):
    # befor 29 service id range was 8000, and service_type_is=21
    for i in range(int(rang)):
        unique_obj = Model.UniqueCodes()
        unique_obj.service_type_id = int(service_id)
        unique_obj.code_type = "Online"
        unique_obj.assigned_to = "PayTM"
        unique_obj.is_distributed = True # Only will be True if redeem pin are created for PayTM
        unique_obj.save()
    return True