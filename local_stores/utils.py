from hv_whatsapp_api.models import question_master, customer_info, customer_lookup, UniqueCodes
from local_stores.models import NavigantUsersDetail, PartnerUsersDetail
from promotional_marketing.models import sent_reminder
from hv_whatsapp_api.hv_whatsapp_backend import send_mail as mail



# Send responce for all End Point
def responsedata(status, message, code=None, data=None,):
    """Method to send data in the given format."""
    if status:
        return {"status":status, "message":message, "code":code, "data":data}
    else:
        return {"status":status, "message":message, "code":code}


def welcome_notification_on_whatsapp(mobile_no):
    try:
        message_content = question_master.objects.filter(question_id=308).last().question_desc_eng
        sid = sent_reminder(str(mobile_no), message_content)
        return True
    except Exception:
        return False  
    
def validate_redeempin_for_strors(redeempin,mobile_no):
    try:
        cust_info = customer_info.objects.filter(mobile_no=mobile_no).last()
        user_detail_obj = NavigantUsersDetail.objects.filter(shared_redeempin=redeempin).last()
        if user_detail_obj:
            user_detail_obj.is_redeempin_redeemed = True
            user_detail_obj.customer_info = cust_info
            user_detail_obj.save()
            session_id = str(cust_info.session_id)
            mail_process = mail.Send_Email()
            subject = "Stores Ticket Notification"
            text = f"Navigant user ({user_detail_obj.name}) redeemed pin {redeempin} with customer info id {session_id}."
            content = text
            mail_process.process(subject,content) 
            return True
        return False
    except Exception:
        return False 
    
def update_cantidate_notification_for_strors(session_id,customer_type=None):
    try:
        if customer_type != None and customer_type == '3':
            cust_lookup_obj = customer_lookup.objects.filter(customer_info = session_id).last()
            stores_info = NavigantUsersDetail.objects.filter(customer_info__session_id=cust_lookup_obj.vendor_id).last()
            if stores_info:
                stores_info.is_process_completed_by_candidate = True
                stores_info.save()
                return True
            return False
        else:    
            stores_info = NavigantUsersDetail.objects.filter(customer_info__session_id=session_id).last()
            if stores_info:
                stores_info.is_invite_sent_to_candidate = True
                stores_info.save()
                return True
            return False
    except Exception:
        return False 


def update_stores_for_report_notification(session_id):
    try:
        cust_lookup_obj = customer_lookup.objects.filter(customer_info = session_id).last()
        stores_info = NavigantUsersDetail.objects.filter(customer_info__session_id=cust_lookup_obj.vendor_id).last()
        if stores_info:
            stores_info.is_report_share_to_client = True
            stores_info.save()
            return True
        return False
    except Exception:
        return False 
    
    
    
def validate_redeempin_for_partners(redeempin,mobile_no):
    try:
        cust_info = customer_info.objects.filter(mobile_no=mobile_no).last()
        uniquecode_detail_obj = UniqueCodes.objects.filter(code=redeempin).last()
        if uniquecode_detail_obj and uniquecode_detail_obj.assigned_to == "PayTM":
            checks = {"21":"Verify Nanny","22":"Verify Driver","23":"Verify Domestic Help/Security Guard","24":"Verify Anyone","25":"Know the Identity","29":"Know your Contact" }
            partner_usersdetail_obj = PartnerUsersDetail()
            partner_usersdetail_obj.source = "PayTM"
            partner_usersdetail_obj.card = checks[str(uniquecode_detail_obj.service_type_id)]
            partner_usersdetail_obj.mobile_num = mobile_no
            partner_usersdetail_obj.shared_redeempin = redeempin
            partner_usersdetail_obj.is_redeempin_redeemed = True
            partner_usersdetail_obj.customer_info = cust_info
            partner_usersdetail_obj.save()
            session_id = str(cust_info.session_id)
            mail_process = mail.Send_Email()
            subject = "PayTM Ticket Notification"
            text = f"Patner user ({partner_usersdetail_obj.name}) redeemed pin {redeempin} with customer info id {session_id}."
            content = text
            mail_process.process(subject,content) 
            return True
        return False
    except Exception:
        return False 
    
def update_cantidate_notification_for_partners(session_id,customer_type=None):
    try:
        if customer_type != None and customer_type == '3':
            cust_lookup_obj = customer_lookup.objects.filter(customer_info = session_id).last()
            stores_info = PartnerUsersDetail.objects.filter(customer_info__session_id=cust_lookup_obj.vendor_id).last()
            if stores_info:
                stores_info.is_process_completed_by_candidate = True
                stores_info.save()
                return True
            return False
        else:    
            stores_info = PartnerUsersDetail.objects.filter(customer_info__session_id=session_id).last()
            if stores_info:
                stores_info.is_invite_sent_to_candidate = True
                stores_info.save()
                return True
            return False
    except Exception:
        return False 


def update_stores_for_report_notification_partners(session_id):
    try:
        cust_lookup_obj = customer_lookup.objects.filter(customer_info = session_id).last()
        stores_info = PartnerUsersDetail.objects.filter(customer_info__session_id=cust_lookup_obj.vendor_id).last()
        if stores_info:
            stores_info.is_report_share_to_client = True
            stores_info.save()
            return True
        return False
    except Exception:
        return False                   
    