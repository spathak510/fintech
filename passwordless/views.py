import json
from rest_framework import status, viewsets
from rest_framework.decorators import (action,   parser_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated
import logging, traceback, inspect
from datetime import datetime, timedelta
from rest_framework.response import Response
from . import models as Model
import secrets
from hv_whatsapp_api.hv_whatsapp_backend import send_mail as mail
from django.shortcuts import HttpResponse, render
from hv_whatsapp import settings as app_settings

class Views(viewsets.ViewSet):
    

    def get_link_html(self, link):
        with open('static/page1.html', 'r') as file:
            data = file.read().replace('\n', '').replace('accept_link', link)

        return data

    # get DL details from processor
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def magic_link(self, payload):
        try:
            payload = payload.data
            url_token = secrets.token_urlsafe(16)
            sec_token = secrets.token_urlsafe(16)
            email = payload.get('email', '')
            Model.MagicLink.objects.create(
                email = email,
                mobile_no=payload.get('mobile_no', ''),
                url_token = url_token,
                sec_token = sec_token,
                is_active = False
                )
            mail_obj = mail.Send_Email()
            subject = 'Login Request'
            link = app_settings.APP_API['MAGIC_EMAIL_URL'] + url_token

            html = self.get_link_html(link)
                                                
            mail_obj.process(subject, html, '', email)
            
            result = {'result': True, 'sec_token':sec_token}
            
            return Response(result, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    # Allow login access
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def link(self, request):
        try:
            # request = request.data
            url_token = request.GET.get('sid', 'NoURL')
            magic_obj = Model.MagicLink.objects.filter(
                url_token=url_token, 
                is_active=False, 
                created_at__gt=datetime.now() - timedelta(seconds=120)
                ).last()
            if magic_obj:
                magic_obj.is_active = True
                magic_obj.save()
                return render(request, 'passwordless/thanks.html', {})
            else:
                return render(request, 'passwordless/expired.html', {})
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Allow login access
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def status(self, payload):
        try:
            email = payload.data.get('email', '')
            sec_token = payload.data.get('sec_token', '')
            magic_obj = Model.MagicLink.objects.filter(
                email=email,
                sec_token=sec_token,
                ).last()
            if magic_obj:
                db_time = magic_obj.created_at.replace(tzinfo=None)
                now = datetime.now().replace(tzinfo=None)
                timediff = now - db_time
                td = int(timediff.total_seconds())
                if magic_obj.is_active == True:                    
                    print('------>', td)
                    if td < 120:
                        magic_obj.is_active = None
                        magic_obj.save()
                        result = {'result': True}
                    else:
                        result = {'result': 'expired'}
                elif td >= 120:
                    result = {'result': 'expired'}
                else:
                    result = {'result': False}            
            else:
                result = {'result': 'expired'}
            
            return Response(result, status = status.HTTP_200_OK)
        except Exception as ex:
            traceback.print_exc()
            logging.warning("<----------"+str(datetime.now())+"---------->")
            logging.exception((inspect.currentframe().f_code.co_name).upper())
            return Response({'result': 'Something went wrong'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)