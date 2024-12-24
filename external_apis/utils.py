from datetime import datetime 
import requests, json, base64
from PIL import Image, ImageDraw

def HitSaver(data):
    from . models import HitRecord
    import pytz    
    timezone = pytz.timezone('Asia/Kolkata')
    HitRecord.objects.create(
                        user=data['user'],
                        api_name=data['api_name'],
                        api_endpoint=data['api_endpoint'],
                        hit_time=datetime.now(),
                        payload=data['payload'],
                        response=data['response'],
    )

def KarzaFunction(user, api_name, url, payload, endpoint_details):
    if 'test' in url:
        headers = {
            endpoint_details['KARZA_API_KEY_ID']:endpoint_details['KARZAAPI_KEY_ADVANCED'],
            'Content-Type': 'application/json'
        }
    else:
        headers = {
            endpoint_details['KARZA_API_KEY_ID']:endpoint_details['KARZAAPI_KEY'],
            'Content-Type': 'application/json'
        }
    response = requests.request("POST", url, headers=headers, data=payload)
    actual_response = json.loads(response.text)
    if 'result' in actual_response:
        if len(actual_response['result'])!=0:
            response = {'status' : True, 'message' : actual_response, 'status_no' : 200}
        elif len(actual_response['result'])==0:
            response = {'status' : False, 'message' : 'No data found for given details', 'status_no' : 400}
    else:
        response = {'status' : False, 'message' : 'API Down.', 'status_no' : 400}
    data = {'user': user, 'api_name':api_name, 'api_endpoint': url, 'payload': payload, 'response':actual_response}
    HitSaver(data)
    return response

def PhoneToUan(phone):
    datas=[]
    if phone != 0:
        url = "https://api.karza.in/v2/uan-lookup"
        payload = json.dumps({
        "consent": "Y",
        "mobile": phone
        })
        headers = {
        'x-karza-key': 'mzgzCYLM9Bxad9zbcif4',
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()

def UanResult(uan, name):
    if name=='' or name ==0:
        name='Helloverify'
    else:
        name=name
    url = "https://api.karza.in/v2/employment-verification"
    headers = {
                'x-karza-key': 'mzgzCYLM9Bxad9zbcif4',
                'Content-Type': 'application/json'
                }
    payload = json.dumps({
                "name": name,
                "uans": [
                    int(uan)
                ],
                "alternateFlow": True
                })
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def UanHandler(phone, uan, name):
    if phone!=0 and uan == 0:
        uan_nos = PhoneToUan(phone)
        try:
            uan_nos = uan_nos['result']['uan']
        except:
            uan_nos = []

        if len(uan_nos)>0:
            uan_data=[]

            for i in uan_nos:
                data = UanResult(i, name)
                try:
                    uan_data.append(data)
                except:
                    uan_data.append({'message':"data not found"})
            return [uan_nos, uan_data]
        
    elif phone==0 and uan != 0:
        result = UanResult(uan, name)
        return [result]
            
def detect_text(content):

    """Detects text in the file."""

    from hv_whatsapp.common_methods import get_secret
    from google.cloud import vision
    from google.oauth2 import service_account
    credentials = service_account.Credentials.from_service_account_info(info=get_secret("GOOGLE_VISION"))

    client = vision.ImageAnnotatorClient(credentials=credentials)
    
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.full_text_annotation.text#response.text_annotations

    return texts




# Marge two dict data into one dict
def margedict(firstdict,seconddict):
    for item in seconddict:
        if item not in firstdict.keys() or firstdict[item]== '' or firstdict[item]== None:
            firstdict[item] = seconddict[item]
    return firstdict


def encode_credentials(username, password):
        """
        Encodes the username and password into a Base64 Basic Authentication string.
        """
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return encoded_credentials

