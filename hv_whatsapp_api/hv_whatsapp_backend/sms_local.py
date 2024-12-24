import logging
import logging
import inspect
from datetime import datetime
import traceback
import threading
from hv_whatsapp import settings as app_settings
from twilio.rest import Client
from hv_whatsapp_api.hv_whatsapp_backend import send_mail
from hv_whatsapp_api import models as Model

logging.basicConfig(filename="error_log.log")

'''
clean message text
'''
def clean_sms_text(text):
    try:
        return text.replace("%", "%25").replace("&", "%26").replace("\"", "%22").replace("'", "%27")
    except Exception as ex:
        traceback.print_exc()
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())

def send_twilio_sms(sender_mobile, sms_text):
    try:
        # Your Account Sid and Auth Token from twilio.com/console
        # and set the environment variables. See http://twil.io/secure
        account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
        auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
        client = Client(account_sid, auth_token)

        message = client.messages.create(
                                    body=sms_text,
                                    from_='+14157924931',
                                    to=sender_mobile
                                )
        return True
    except Exception as ex:
        # print(str(ex))
        # traceback.print_exc()
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())
'''
send otp message to customer using ozontal service
'''
def sendSMS(sender_mobile, sms_text):
    try:
        send_twilio_sms(sender_mobile, sms_text)

        return True

    except Exception as ex:
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())

'''
prepare message to send with otp
'''
def send_registration_otp_msg(sender_mobile, otp):
    try:
        sendSMS(sender_mobile,f'Dear User, Welcome to Hello Verify WhatsApp Program. \nYour OTP for verifying your mobile number is {otp}')
        t1 = threading.Thread(target=send_otp_email, args=(sender_mobile, otp,))
        t1.start()
    except Exception as ex:
        traceback.print_exc()
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())

def send_otp_email(sender_mobile, otp):
    try:
        verify_now_obj = Model.VerifyNow.objects.filter(mobile_no=sender_mobile, is_redemption_pin_shared=True).exclude(email=None).order_by('-id')
        if verify_now_obj:
            mail_obj = send_mail.Send_Email()
            subject = "Welcome to Helloverify"
            content = f"Dear User, Welcome to Hello Verify WhatsApp Program. <br><br>Your OTP for verifying your mobile number is {otp}"
            mail_obj.process(subject, content, '', str(verify_now_obj[0].email))
    except Exception as ex:
        traceback.print_exc()
        logging.warning("<----------"+str(datetime.now())+"---------->")
        logging.exception((inspect.currentframe().f_code.co_name).upper())