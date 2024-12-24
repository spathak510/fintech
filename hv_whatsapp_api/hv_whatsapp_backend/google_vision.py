import os, json
from google.cloud import vision, translate
import urllib.request
import time

import logging
import inspect
from datetime import datetime
import traceback
from . import send_mail as mail
from hv_whatsapp.common_methods import get_secret
from google.oauth2 import service_account


logging.basicConfig(filename="error_log.log")


class Image_to_Ocr_text:
    def __init__(self):
        self.count = 0

    '''
    google vision api to detect the text from the image
    '''
    def detect_text_img(self, path):
        try:
            """Detects text in the file.""" #
            from google.cloud import vision
            import io

            # print("PATH:",path)
            # credential_path = "hv_whatsapp/google_vision_key.json"
            # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
            service_account_creds = service_account.Credentials.from_service_account_info(info=get_secret("GOOGLE_VISION"))

            client = vision.ImageAnnotatorClient(credentials=service_account_creds)

            with io.open(path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)

            response = client.text_detection(image=image)
            texts = response.full_text_annotation.text#response.text_annotations
            print('Texts:',texts)

            if response.error.message:
                raise Exception(
                    '{}\nFor more info on error messages, check: '
                    'https://cloud.google.com/apis/design/errors'.format(
                        response.error.message))
            return texts
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    retry the google vision api if any fail occurs
    '''
    def parsing_retry(self, image_url):
        try:
            urllib.request.urlretrieve(image_url, "img.jpg")
            str_ocr = self.detect_text_img("img.jpg")
            return str_ocr
        except Exception as e:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return False

    '''
    google vision api to detect the text from the image url
    '''
    def detect_text_uri(self, url):
        """Detects text in the file located in Google Cloud Storage or on the Web.
        """
        try:
            # credential_path = "hv_whatsapp/google_vision_key.json"
            # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

            service_account_creds = service_account.Credentials.from_service_account_info(info=get_secret("GOOGLE_VISION"))
            client = vision.ImageAnnotatorClient(credentials=service_account_creds)

            client = vision.ImageAnnotatorClient(credentials=service_account_creds)
            image = vision.Image()
            image.source.image_uri = url

            response = client.text_detection(image=image)
            if 'Connection aborted' in str(response):
                # send mail
                mail_process = mail.Send_Email()
                subject = "OCR Not working"
                content = "OCR ISSue"
                mail_process.process(subject,content)
            str_ocr = response.full_text_annotation.text
            if response.error.message:
                print('I am from second google vision api')
                str_ocr = self.parsing_retry(url)
            return str_ocr
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            self.parsing_retry(url)

    '''
    translate the text from google vision api
    '''
    def translate_text(self,text,target='hi'):
        try:
            # credential_path = "hv_whatsapp\\vision_api_key.json"/
            # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
            service_account_creds = service_account.Credentials.from_service_account_info(info=get_secret("GOOGLE_VISION"))
            translate_client = translate.Client(credentials=service_account_creds)
            result = translate_client.translate(
                text,
                target_language=target)
            return result['translatedText']
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
    

