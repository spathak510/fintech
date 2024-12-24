from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import smtplib
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders
import os
import logging
import inspect
from datetime import datetime
import traceback

logging.basicConfig(filename="error_log.log")

class Send_Email():        
    '''
    send mail to admin and other users for errors and report generation 
    '''
    def process(self, subject, content, filename = '', email_to = ''):
        try:
            msg = EmailMessage()
            part2 = MIMEText(content, 'html')
            msg.make_alternative()
            msg.attach(part2)
            msg['Subject'] = subject
            if 'error_log' in subject:
                error_file= open("/home/hello/proj_id_check/fintech_backend/error_log.log","r+")
                # create a backup of error log file
                backup_error_log = open("/home/hello/proj_id_check/fintech_backend/backup_error_log.log","a+")
                backup_error_log.write("\n" + error_file.read()) 
                backup_error_log.close()
                error_file.truncate(0)
                error_file.close()
            s = smtplib.SMTP(host="smtp.office365.com", port=587)
            s.starttls()
            if 'Manual Crime Check' in subject:
                msg['From'] = 'hellov@helloverify.com'
                # msg['To'] = 'saurabh.verma@helloverify.com'
                msg['To'] = 'Jitendra.roy@Helloverify.com, Pradeep.Verma@Helloverify.com'
                msg['Cc'] = 'Pradeep.Verma@Helloverify.com, neha.rathore@partner.helloverify.com, arpita.mathur@helloverify.com, sono.pathak@helloverify.com'
                s.login('hellov@helloverify.com', 'Password@8899000')
            else:
                if "Received Payment" in subject:
                    msg['From'] = 'hellov@Helloverify.com'
                    msg['To'] = 'vm@helloverify.com, varun.saini@helloverify.com'
                    # msg['To'] = 'neha.rathore@partner.helloverify.com'        
                    msg['Cc'] = 'Pradeep.Verma@Helloverify.com, neha.rathore@partner.helloverify.com, arpita.mathur@helloverify.com, sono.pathak@helloverify.com'
                    s.login('hellov@Helloverify.com', 'Password@8899000')
                elif 'Hellov report sent successfully' in subject:
                    attachment = open(filename, "rb")
                    p = MIMEBase('application', 'octet-stream')  
                    p.set_payload((attachment).read()) 
                    encoders.encode_base64(p) 
                    p.add_header('Content-Disposition', "attachment; filename=fname".replace('fname', filename.split('/')[-1]))
                    msg.attach(p)
                    msg['From'] = 'hellov@Helloverify.com'        
                    msg['To'] = 'vm@helloverify.com, varun.saini@helloverify.com'
                    #msg['To'] = 'sono.pathak@helloverify.com'
                    msg['Cc'] = 'Pradeep.Verma@Helloverify.com, neha.rathore@partner.helloverify.com, arpita.mathur@helloverify.com, sono.pathak@helloverify.com'
                    s.login('hellov@Helloverify.com', 'Password@8899000')
                elif "Welcome to Helloverify" in subject:
                    msg['From'] = 'hellov@Helloverify.com'
                    msg['To'] = email_to
                    s.login('hellov@Helloverify.com', 'Password@8899000')
                
                elif "Aadhaar automat report process" in subject or "Report process automation error" in subject:
                    msg['From'] = 'hellov.error@Helloverify.com'
                    msg['To'] = 'neha.rathore@partner.helloverify.com, sono.pathak@helloverify.com'
                    s.login('hellov.error@Helloverify.com', 'Password@10')
                    
                elif "Stores Ticket Notification" in subject:
                    msg['From'] = 'hellov@Helloverify.com'
                    msg['To'] = 'Suraj.Tiwari@Helloverify.com'
                    msg['Cc'] = 'Pradeep.Verma@Helloverify.com, Nitin.Garg@Helloverify.com, sono.pathak@helloverify.com'
                    s.login('hellov@Helloverify.com', 'Password@8899000')    
                        
                # elif "Welcome to Helloverify - Order ID:" in subject:
                #     msg['From'] = 'hellov@Helloverify.com'
                #     msg['To'] = email_to
                #     s.login('hellov@Helloverify.com', 'Password@8899000')
                # elif "NoBroker" in subject:
                #     msg['From'] = 'hellov@Helloverify.com'
                #     msg['To'] = 'vm@helloverify.com'
                #     # msg['To'] = 'saurabh.verma@helloverify.com'
                #     msg['Cc'] = 'varun.saini@helloverify.com, saurabh.verma@helloverify.com, Aditi.Mainwal@Helloverify.com'
                #     s.login('hellov@Helloverify.com', 'Password@8899000')
                else:
                    msg['From'] = 'hellov.error@Helloverify.com'
                    if 'Report Check Created' in subject:
                        msg['To'] = ' neha.rathore@partner.helloverify.com, sono.pathak@helloverify.com'
                    else:
                        msg['To'] = ' neha.rathore@partner.helloverify.com, sono.pathak@helloverify.com'

                    s.login('hellov.error@Helloverify.com', 'Password@10')
            try:
                s.send_message(msg)
                print ("Successfully sent email")
                return True
            except:
                print ("Error: Somthing went wrong in sending email or saving email")
                traceback.print_exc()
                logging.warning("<----------"+str(datetime.now())+"---------->")
                logging.exception((inspect.currentframe().f_code.co_name).upper())
                return False
            return True
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False
     
# subject = "TEST MAIL"
# content = "<html>Please do manual crime check within 5 hours for order id: e770f1241764a4a9\n\nhttp://52.66.35.239:8007/Account/Login \nPlease check below IDs for your reference: \nFront Image URL: https://s3-external-1.amazonaws.com/media.twiliocdn.com/ACdca0e8e83c002ca63cd670ee736fccd6/2a5025a7745c4bd7e265293baad555df \nBack Image URL: https://s3-external-1.amazonaws.com/media.twiliocdn.com/ACdca0e8e83c002ca63cd670ee736fccd6/68c658761fca87da785201fa3674c694 "
# obj = Send_Email()
# obj.process(subject,content)