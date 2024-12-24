from django.db.models.signals import post_save
from django.dispatch import receiver
from hv_whatsapp_api.models import customer_info, order, adhaar_result, report_check
from hv_whatsapp_api.utils import calculat_age_band, number_masking, gender_desider, aadhaar_color_code
import json
from hv_whatsapp_api.hv_whatsapp_backend import send_mail as mail

@receiver(post_save, sender=customer_info)
def aadhaar_automation(sender, instance, *args, **kwargs):
    
    '''post save signal customer_info for prepar data to aadhaar_result'''

    sender_obj = sender.objects.filter(session_id= instance.session_id).last()
    if sender_obj and instance.aadhaar_verification_response:
        try:
            order_obj = order.objects.filter(customer_info=sender_obj).last()
            if order_obj and not adhaar_result.objects.filter(order=order_obj).exists():
                aadhaar_verification_response = json.loads(sender_obj.aadhaar_verification_response) 
                
                request_sent = {
                    'uid_no': str(aadhaar_verification_response['aadhaar_number'])
                    }       
                api_result = {
                    "status": "Success", 
                    "address": str(aadhaar_verification_response['address']['state']), 
                    "ageBand": calculat_age_band(aadhaar_verification_response['dob']), 
                    "gender": gender_desider(aadhaar_verification_response['gender']), 
                    "maskedMobileNumber": number_masking(sender_obj.mobile_no), 
                    "statusMessage": str(aadhaar_verification_response['aadhaar_number'])+" "+"Exists", 
                    "aadhaarStatusCode": "1", 
                    "dob": str(aadhaar_verification_response['dob']), 
                    "mobileNumber": 'null', 
                    "pincode": str(aadhaar_verification_response['zip'])
                    }
                api_result_for_report = {
                    "age": calculat_age_band(aadhaar_verification_response['dob']),
                    "gender": gender_desider(aadhaar_verification_response['gender']),
                    "state": str(aadhaar_verification_response['address']['state']), 
                    "mobile": number_masking(sender_obj.mobile_no)
                    }
                rule_engine_result = {
                    "uid": 'true', 
                    "state": 'true' if str(aadhaar_verification_response['address']['state']) else None, 
                    "age_range": 'true' if calculat_age_band(aadhaar_verification_response['dob']) else None, 
                    "gender": 'true' if gender_desider(aadhaar_verification_response['gender']) else None, 
                    "dob": 'true' if calculat_age_band(aadhaar_verification_response['dob']) else None
                    }
                is_check_passed = 1
                color_code = aadhaar_color_code(rule_engine_result)
                aadhaar_result_obj = adhaar_result.objects.create(order=order_obj,request_sent=request_sent,\
                    api_result=json.dumps(api_result),api_result_for_report=json.dumps(api_result_for_report),rule_engine_result=json.dumps(rule_engine_result),\
                        is_check_passed=is_check_passed,color_code=color_code )
                
                # if aadhaar_result_obj and report_check.objects.filter(order=order_obj).exists():
                #     report_check_obj = report_check.objects.filter(order=order_obj.order_id).last()
                #     report_check_obj.init_qc_done = True
                #     report_check_obj.id_check_status = True
                #     report_check_obj.save() 
            else:
                return False    
        except Exception as ex:
            mail_process = mail.Send_Email()
            subject = "Aadhaar automat report process"
            content = str(ex.text)
            mail_process.process(subject,content)                      
    return True


@receiver(post_save, sender=report_check)
def report_check_automation(sender, instance, *args, **kwargs):
    
    '''post save signal for report automation with report generate and review'''
    try:
        sender_obj = sender.objects.filter(order=instance.order).last()
        report_check_obj = ''
        if sender_obj and instance.order.customer_info.adhaar_number and instance.report_status == "0" and instance.init_qc_done != True:
            report_check_obj = report_check.objects.filter(order=sender_obj.order).last()
            report_check_obj.id_check_status = True
            report_check_obj.init_qc_done = True    
            report_check_obj.save() 
            return True
        
        elif sender_obj and instance.order.customer_info.dl_number and instance.report_status == "0" and instance.init_qc_done != True:
            report_check_obj = report_check.objects.filter(order=sender_obj.order).last()
            report_check_obj.init_qc_done = True    
            report_check_obj.save() 
            return True    
            
    except Exception as ex:
        mail_process = mail.Send_Email()
        subject = "Report process automation error"
        content = str(ex.text)
        mail_process.process(subject,content)
        return False
            


def aadhaar_automation_seven(session_id):
    
    '''post save signal customer_info for prepar data to aadhaar_result'''

    sender_obj = customer_info.objects.filter(session_id= session_id).last()
    if sender_obj and sender_obj.aadhaar_verification_response:
        try:
            order_obj = order.objects.filter(customer_info=sender_obj).last()
            if order_obj and not adhaar_result.objects.filter(order=order_obj).exists():
                aadhaar_verification_response = json.loads(sender_obj.aadhaar_verification_response) 
                
                request_sent = {
                    'uid_no': str(aadhaar_verification_response['aadhaar_number'])
                    }       
                api_result = {
                    "status": "Success", 
                    "address": str(aadhaar_verification_response['address']['state']), 
                    "ageBand": calculat_age_band(aadhaar_verification_response['dob']), 
                    "gender": gender_desider(aadhaar_verification_response['gender']), 
                    "maskedMobileNumber": number_masking(sender_obj.mobile_no), 
                    "statusMessage": str(aadhaar_verification_response['aadhaar_number'])+" "+"Exists", 
                    "aadhaarStatusCode": "1", 
                    "dob": str(aadhaar_verification_response['dob']), 
                    "mobileNumber": 'null', 
                    "pincode": str(aadhaar_verification_response['zip'])
                    }
                api_result_for_report = {
                    "age": calculat_age_band(aadhaar_verification_response['dob']),
                    "gender": gender_desider(aadhaar_verification_response['gender']),
                    "state": str(aadhaar_verification_response['address']['state']), 
                    "mobile": number_masking(sender_obj.mobile_no)
                    }
                rule_engine_result = {
                    "uid": 'true', 
                    "state": 'true' if str(aadhaar_verification_response['address']['state']) else None, 
                    "age_range": 'true' if calculat_age_band(aadhaar_verification_response['dob']) else None, 
                    "gender": 'true' if gender_desider(aadhaar_verification_response['gender']) else None, 
                    "dob": 'true' if calculat_age_band(aadhaar_verification_response['dob']) else None
                    }
                is_check_passed = 1
                color_code = aadhaar_color_code(rule_engine_result)
                aadhaar_result_obj = adhaar_result.objects.create(order=order_obj,request_sent=request_sent,\
                    api_result=json.dumps(api_result),api_result_for_report=json.dumps(api_result_for_report),rule_engine_result=json.dumps(rule_engine_result),\
                        is_check_passed=is_check_passed,color_code=color_code )
            else:
                return False    
        except Exception as ex:
            mail_process = mail.Send_Email()
            subject = "Aadhaar automat report process"
            content = str(ex.text)
            mail_process.process(subject,content)                      
    return True   