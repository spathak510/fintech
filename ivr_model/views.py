from django.shortcuts import render
from hv_whatsapp import settings as app_settings
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from local_stores.utils import responsedata
from datetime import date, timedelta
from django.http import HttpResponse
from twilio.twiml.voice_response import Gather, VoiceResponse
from twilio.rest import Client
from django.views.decorators.csrf import csrf_exempt
from hv_whatsapp_api.models import customer_lookup
from ivr_model.models import IVRCondidateTracker
from rest_framework.decorators import (action,)
from hv_whatsapp_api.hv_whatsapp_backend import processor
from hv_whatsapp_api import models as hvmodel



    
def ivr_calling_to_complete_process():
    import time
    today = date.today() - timedelta(days = 1)
    candidate_lookup_queryset = customer_lookup.objects.filter(created_at__date=today)
    if candidate_lookup_queryset:
        for obj in candidate_lookup_queryset:
            if obj.customer_info.address == '' or not obj.customer_info.dob or obj.customer_info.father_name == '':
                # user_type = 'CONDIDATE'
                to_number = obj.candidate_mobile
                cid =  obj.customer_info_id
                res = make_outgoing_call(cid, to_number)
            continue
    return True


@csrf_exempt
def create_language_selection_twiml(request,cid):
    obj = customer_lookup.objects.get(customer_info__session_id=cid)
    candidate = obj.candidate_name
    
    response = VoiceResponse()
    gather = Gather(action='/ivr/handle-language-selection/'+str(cid), method='POST', num_digits=1)
    # gather.say("Press 1 for English. Press 2 for Hindi.")
    gather.say(f"Dear {candidate}, This is a follow-up call from Helloverify Press 1 for English, हिंदी के लिए 2 दबाएं।")
    response.append(gather)
    return HttpResponse(str(response), content_type='text/xml')




def make_outgoing_call(cid, to_number):
    try:
        account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
        auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
        twilio_number = "+14157924931"

        client = Client(account_sid, auth_token)

        call = client.calls.create(
            url='https://checkapi.helloverify.com/ivr/select-language/'+str(cid),  # URL for language selection
            to=to_number,
            from_=twilio_number,
            method='POST'
        )
        
        print("Outgoing call initiated.")
        return True, call.sid
    except Exception as ex:
        print(f'Error initiating call: {str(ex)}')
        return False, None
    
    
    
@csrf_exempt
def handle_language_selection(request,cid):
    obj = customer_lookup.objects.get(customer_info__session_id=cid)
    vendor = obj.vendor_name 

    digit_pressed = request.POST.get('Digits', None)
    response = VoiceResponse()

    english_prompt = f"This call is regarding your background verification requested by {vendor}. Your document upload is pending since yesterday. The verification link has a validity of 72 hours from the time of issue. Please choose an option: Press 1 to complete the process, or Press 2 if you do not want to proceed with this background check."
    if digit_pressed == '1':
        response.say(english_prompt)
        gather = Gather(action='/ivr/handle-input-english/'+str(cid), method='POST', num_digits=1)
        gather.say("Please enter a digit.")
        response.append(gather)
    elif digit_pressed == '2':
        # response.say("आपने हिंदी चुनी है।")
        hindi_prompt = f"प्यह HelloVerify की ओर से {vendor} द्वारा अनुरोधित आपके Background Verification के संबंध में एक  कॉल है। आपका दस्तावेज़ अपलोड कल से अपूर्ण है। Verification लिंक की वैधता जारी होने के समय से बहत्तर घंटे है। एक विकल्प का चयन करें:प्रक्रिया पूरी करने के लिए एक दबाएँ, या यदि आप आगे नहीं बढ़ना चाहते हैं तो दो दबाएँ।"
        response.say(hindi_prompt)
        gather = Gather(action='/ivr/handle-input-hindi/'+str(cid), method='POST', num_digits=1)
        gather.say("कृपया एक अंक दर्ज करें।")
        response.append(gather)
    else:
        response.say("Invalid selection. Please try again.")
        response.redirect('/ivr/select-language/'+str(cid))

    return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def handle_input_english(request, cid):
    digit_pressed = request.POST.get('Digits', None)
    IVRCondidateTracker.objects.create(customer_lookup=str(cid),is_processed=int(digit_pressed))
    
    response = VoiceResponse()

    if digit_pressed:
        response.say(f"You entered {digit_pressed}. Thank you!")
    else:
        response.say("Invalid input. Please try again.")
        response.redirect('/ivr/handle-language-selection/'+str(cid))

    return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
def handle_input_hindi(request, cid):
    digit_pressed = request.POST.get('Digits', None)
    IVRCondidateTracker.objects.create(customer_lookup=str(cid),is_processed=int(digit_pressed))
    
    response = VoiceResponse()

    if digit_pressed:
        response.say(f"आपने {digit_pressed} दर्ज किया। धन्यवाद!")
    else:
        response.say("अमान्य इनपुट। कृपया पुन: प्रयास करें।")
        response.redirect('/ivr/handle-language-selection/'+str(cid))

    return HttpResponse(str(response), content_type='text/xml')    





class IVRCalling(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        # from hv_whatsapp_api.hv_whatsapp_backend import processor
        # from hv_whatsapp_api.models import order
        # obj = order.objects.filter(customer_info__session_id=12299).last()
        # final_msg = "Incomplete report."
        # url = obj.report_url
        # send_msg = processor.DB_Processor()
        # send_msg.sent_reminder('+919411287010', final_msg,url=url)
        ivr_calling_to_complete_process()
        return Response(responsedata(True,"Notification sent on your whats'app." , 200),status=status.HTTP_200_OK)


def index(request):
    import json
    from hv_whatsapp_api.models import report
    print("Render adhaar badge template..........")
    obj = report.objects.filter(order="33C89612305").last()
    context = {
        'title': 'Welcome to My Django App',  # Assuming you're using Django's built-in authentication
        'jsn':json.loads(obj.report_json)
    }
    return render(request, 'hv_whatsapp_api/reports/dl_badge.html', context)