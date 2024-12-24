from django.db import models

# Create your models here.

class Promotional_marketingBasemodel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, editable=False) 
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=False) 
    
    class Meta:
        abstract = True



class PromotionalData(Promotional_marketingBasemodel):
    csv_file = models.FileField(upload_to='promotional-csv',null=False,blank=False)
    batch_size = models.BigIntegerField(null=False,blank=False,default=200)
    message_sent = models.BigIntegerField(null=False,blank=False,default=0)
    send_all_at_once = models.BooleanField(default=False)
    is_data_imported = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return str(self.csv_file)

class PromotionalMessageTracker(Promotional_marketingBasemodel):
    STATUSES = (('READ','READ'),('DELIVERED','DELIVERED'),('FAILED','FAILED'),('READ','READ'),('RECEIVED','RECEIVED'),('SENT','SENT'),('UNDELIVERED','UNDELIVERED'),('--','--'))
    mobile_no = models.BigIntegerField(null=False,blank=False)
    message_code = models.BigIntegerField(null=False,blank=False)
    is_purchased = models.BooleanField(default=False)
    last_purchase_date = models.DateTimeField(null=True, blank=True)
    message_sid = models.CharField(max_length=100, null=True, blank=True, editable=False)
    msg_status = models.CharField(max_length=100,choices=STATUSES ,default='--')
    from_file = models.ForeignKey(to='promotional_marketing.PromotionalData',null=True,blank=True,on_delete=models.SET_NULL)
    is_message_sent_once = models.BooleanField(default=False)
    send_force = models.BooleanField(default=False)
    class Meta:
        ordering = ['-updated_at']

from django.db.models.signals import post_save
from django.dispatch import receiver
from promotional_marketing.models import PromotionalMessageTracker
import datetime, time, logging, inspect
from hv_whatsapp import settings as app_settings
from hv_whatsapp_api.models import question_master


def sent_reminder(mobile, mesg, url=None):
    try:
        from twilio.rest import Client
        account_sid = app_settings.EXTERNAL_API['TWILIO_SID']
        auth_token = app_settings.EXTERNAL_API['TWILIO_KEY']
        client = Client(account_sid, auth_token)

        message = client.messages \
            .create(
                media_url=[url],
                from_='whatsapp:+14157924931',
                body=mesg,
                to='whatsapp:+'+mobile
            )
        f = open("marketing.log", "a")
        f.write("<----------"+str(datetime.datetime.now())+"---------->\n\n")
        f.write("<----------"+str(mobile)+" SID:"+str(message.sid)+"---------->\n")
        f.close()
        # return("Khali")
        return (str(message.sid))
    except Exception as ex:
        f = open("marketing.log", "a")
        f.write("<----------"+str(datetime.datetime.now())+"---------->\n\n")
        f.write("<----------"+str(ex)+"---------->\n")
        f.close()
        return str(ex)


def send_whatsapp_on_save(instance):
    if not instance.is_message_sent_once:
        try:
            message_content = question_master.objects.filter(question_id=instance.message_code).last().question_desc_eng
            sid = sent_reminder(str(instance.mobile_no), message_content)
            instance.message_sid=sid
            instance.is_message_sent = True
            instance.save()
        except Exception as ex:
            f = open("marketing.log", "a")
            f.write("<----------"+str(datetime.datetime.now())+"---------->\n")
            f.write("<----------"+str(ex)+"---------->\n")
            f.close()
   

@receiver(post_save, sender=PromotionalMessageTracker)
def send_whatsapp_force(sender, instance, created, **kwargs):
    if instance.send_force:
        try:
            message_content = question_master.objects.filter(question_id=instance.message_code).last().question_desc_eng
            sid = sent_reminder(str(instance.mobile_no), message_content)
            instance.message_sid = sid
            instance.send_force = False
            instance.is_message_sent_once = True   
            instance.save()
        except Exception as ex:
            f = open("marketing.log", "a")
            f.write("<----------"+str(datetime.datetime.now())+"---------->\n")
            f.write("<----------"+str(ex)+"---------->\n")
            f.close()

        