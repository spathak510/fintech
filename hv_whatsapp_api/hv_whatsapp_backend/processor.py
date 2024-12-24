import datetime 
from hv_whatsapp_api import models as Model
import threading
import time
from django.utils.timezone import utc
from retrying import retry
from hv_whatsapp import settings as app_settings

import logging
import inspect
import traceback

logging.basicConfig(filename="error_log.log")

class DB_Processor():

    # Find difference between updated time and current time        
    def find_time_difference_in_minutes(self, db_time):
        try:
            db_time = db_time.replace(tzinfo=None)
            now = datetime.datetime.now().replace(tzinfo=None)#datetime.datetime.utcnow().replace(tzinfo=utc)
            timediff = now - db_time
            td = timediff.total_seconds()//60
            return int(td)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex


    # Send reminder to particular whatsapp number
    @retry(stop_max_attempt_number=4, wait_random_min=2000, wait_random_max=3000)
    def sent_reminder(self,mobile, mesg, url=None):
        try:
            from twilio.rest import Client
            account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
            auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
            client = Client(account_sid, auth_token)
            if app_settings.LOCAL_ENV == False:
                message = client.messages \
                    .create(
                        media_url=[url],
                        from_='whatsapp:+14157924931',
                        body=mesg,
                        to='whatsapp:'+mobile
                    )
            else:
                message = client.messages \
                    .create(
                        media_url=[url],
                        from_='whatsapp:+14155238886',
                        body=mesg,
                        to='whatsapp:'+mobile
                    )
            # message_status = client.messages(message.sid).fetch()        
            return ''
        except Exception as ex:
            raise Exception("Broken twilio api")
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    
    # Check reminder scheduler for customers
    def check_reminders_scheduler(self, mobile, s_time):

        try:
            i=0
            while(i<25):
                time.sleep(s_time)
                i += 4
            # find batch for reminder_type = payment
                batch = Model.Reminder.objects.filter(reminder_type = 0)
                for item in batch:
                    time_diff = self.find_time_difference_in_minutes(item.updated_at)
                    if time_diff in range(10,13):
                        self.sent_reminder(mobile,"Please make payment")
                    elif time_diff in range(20,23):
                        self.sent_reminder(mobile,"Please make payment - reminder 2")
                    elif time_diff in range(30,500):
                        print(item.customer_info)
                        Model.session_log.objects.filter(customer_info = item.customer_info).delete()
                        self.sent_reminder(mobile,"Session Expire")
                    else:
                        pass

                # find batch for reminder_type = verification ( This is only for verification through someone else)
                batch = Model.Reminder.objects.filter(reminder_type = 1)
                for item in batch:
                    time_diff = self.find_time_difference_in_minutes(item.updated_at)
                    if time_diff in range(24*60,24*60+2):
                        self.sent_reminder(item.mobile,"Please complete process")
                    elif time_diff in range(48*60,48*60+2):
                        self.sent_reminder(item.mobile,"Please complete process")
                    elif time_diff in range(71*60,71*60+2):
                        self.sent_reminder(item.mobile,"Please complete process")
                    elif time_diff in range(72*60,80*60):
                        Model.session_log.objects.filter(customer_info = item.customer_info).delete()
                        self.sent_reminder(item.mobile,"Session Expire")
                    else:
                        pass

                return True

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    # create thread to run process parallely
    def create_thread(self, mobile, mesg):
        try:
            t1 = threading.Thread(target=self.sent_reminder, args=(mobile, mesg,))
            t1.start()
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())


    # save new reminder into table
    def save_entry_to_reminder_table(self,payload):

        try:
            session_id = payload["session_id"]
            # Add reminder data for the session_id
            # Fetch customer information for particular session_id
            cust_obj = Model.customer_info.objects.get(session_id = session_id)

            # payment is not done send payment reminder
            if cust_obj.payment_status == 0: #
                reminder_obj = Model.reminder() # create reminder class object
                reminder_obj.customer_info = cust_obj
                reminder_obj.reminder_type = 0
                reminder_obj.mobile_no = cust_obj.mobile_no
                reminder_obj.status = 0 # incomplete
                reminder_obj.reminder_counter = 0
                reminder_obj.save()
                
            # payment done send verification reminder
            elif cust_obj.payment_status == 1:

                if cust_obj.customer_type == '3' or cust_obj.customer_type == '2':
                    reminder_obj = Model.reminder() # create reminder class object
                    reminder_obj.customer_info = cust_obj
                    reminder_obj.reminder_type = 1
                    reminder_obj.mobile_no = cust_obj.mobile_no
                    reminder_obj.status = 0 # incomplete
                    reminder_obj.reminder_counter = 0
                    reminder_obj.save()

            else:
                pass

            return True

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    # delete reminders data from table
    def delete_entry_from_reminder_table(self,session_id):
        try:
            # Delete entry from reminder data for the session_id
            reminder_obj = Model.Reminder.objects.filter(customer_info = session_id).delete()
            return True

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())

    