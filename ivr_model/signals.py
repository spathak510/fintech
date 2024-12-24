from django.db.models.signals import post_save
from django.dispatch import receiver
from ivr_model.models import IVRCondidateTracker
from hv_whatsapp_api import models as hvmodel
from hv_whatsapp_api.hv_whatsapp_backend import processor


@receiver(post_save, sender=IVRCondidateTracker)
def report_check_automation(sender, instance, *args, **kwargs):
    
    '''post save signal for report automation with report generate and review'''
    try:
        obj = IVRCondidateTracker.objects.filter(id=instance.id).last()
        if instance.is_processed:
            order_obj = hvmodel.order.objects.filter(customer_info__session_id=obj.customer_lookup).last()
            clp_obj = hvmodel.customer_lookup.objects.filter(customer_info__session_id=obj.customer_lookup).last()
            vendor_name = clp_obj.vendor_name
            candidate_name = clp_obj.candidate_name
            vendor_mobile_num = clp_obj.vendor_mobile
            candidate_mobile_num = clp_obj.candidate_mobile
            if not obj:
                obj = IVRCondidateTracker()
                obj.is_processed = 0
                
                ques_obj = hvmodel.question_master.objects.filter(question_id=1114).last()
                final_msg = ques_obj.question_desc_eng.format(vendor=vendor_name,candidate=candidate_name,order=order_obj.order_id)
                send_msg = processor.DB_Processor()
                send_msg.sent_reminder(vendor_mobile_num, final_msg)
                # obj.vendor_update = True
                # obj.save()
                return True
                
            elif obj and obj.is_processed == 2:
                ques_obj = hvmodel.question_master.objects.filter(question_id=1114).last()
                final_msg = ques_obj.question_desc_eng.format(vendor=vendor_name,candidate=candidate_name,order=order_obj.order_id)
                send_msg = processor.DB_Processor()
                send_msg.sent_reminder(vendor_mobile_num, final_msg)
                # obj.vendor_update = True
                # obj.save()
                return True
                
            elif obj and obj.is_processed == 1:
                ques_obj = hvmodel.question_master.objects.filter(question_id=1113).last()
                final_msg = ques_obj.question_desc_eng.format(vendor=vendor_name,candidate=candidate_name,order=order_obj.order_id)
                send_msg = processor.DB_Processor()
                send_msg.sent_reminder(candidate_mobile_num, final_msg)
                # obj.save()
                return True
        return True
    except Exception as ex:
            print(str(ex))