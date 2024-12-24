from anticaptchaofficial.imagecaptcha import *
import base64

import logging
import inspect
from datetime import datetime
import traceback

logging.basicConfig(filename="error_log.log")


class GetCaptcha():
    '''
    get captcha text from anticaptcha by passing captcha image
    '''
    def get_captcha_text(self, uid_no):
        try:
            img_name = uid_no + '.jpg'
            solver = imagecaptcha()
            solver.set_verbose(1)
            # solver.set_key("1b1deef3edbd80b6b822eaf575ab9d14")
            solver.set_key("0ce96c65453198c61b6b9a42e10547f5")
            captcha_text = solver.solve_and_return_solution(img_name)
            if captcha_text != 0:
                print("captcha text "+captcha_text)
                return captcha_text
            else:
                print("task finished with error "+solver.error_code)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex

    '''
    download the captcha from UID and PARIVAHAN portal
    '''
    def download_captcha(self, driver, id_type, uid_no):
        try:
            # driver = webdriver.Chrome(executable_path="D:\Projects_django\sel\chromedriver\chromedriver.exe")
            # driver.set_script_timeout(10)
            # driver.get("https://resident.uidai.gov.in/verify")
            if id_type == 'dl':
                # ele_captcha = driver.find_element_by_xpath("//*[@id='form_rcdl:j_idt32:j_idt38']")
                ele_captcha = driver.find_element_by_xpath("//*[@id='form_rcdl:j_idt29:j_idt34']")
            else:#Aadhaar
                img_name = uid_no + '.jpg'
                ele_captcha = driver.find_element_by_xpath("//*[@id='captcha-img']")

            # get the captcha as a base64 string
            img_captcha_base64 = driver.execute_async_script("""
                var ele = arguments[0], callback = arguments[1];
                ele.addEventListener('load', function fn(){
                ele.removeEventListener('load', fn, false);
                var cnv = document.createElement('canvas');
                cnv.width = this.width; cnv.height = this.height;
                cnv.getContext('2d').drawImage(this, 0, 0);
                callback(cnv.toDataURL('image/jpeg').substring(22));
                }, false);
                ele.dispatchEvent(new Event('load'));
                """, ele_captcha)

            # save the captcha to a file
            with open(img_name, 'wb') as f:
                f.write(base64.b64decode(img_captcha_base64))

        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return ex