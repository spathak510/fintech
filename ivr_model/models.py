from django.db import models
from hv_whatsapp_api.models import ops_trackable_model, customer_lookup

class IVRCondidateTracker(ops_trackable_model):
    customer_lookup = models.CharField(max_length=150,null=False,blank=False)
    is_processed = models.IntegerField(null=True, blank=True)
    twilio_call_sid = models.CharField(max_length=255,null=True,blank=True)
    call_status = models.CharField(max_length=200,null=True,blank=True)
    vendor_update = models.BooleanField(null=True,blank=True)
    incomplete_report_send = models.BooleanField(default=None,null=True, blank=True)
    incomplete_report_url = models.CharField(max_length=200, null=True,blank=True)
    status = models.BooleanField(default=None,null=True, blank=True)
    
    
    def __str__(self):
        return self.customer_lookup
    
    class Meta:
        db_table = 'ivr_condidate_tracker'
