from django.db import models
from local_stores.models import BaseModel
from hv_whatsapp_api.models import report_check






class FeedbackLinkValidation(BaseModel):
    report_check = models.ForeignKey(report_check, on_delete=models.DO_NOTHING, null=False, blank=False)
    link_url = models.CharField(max_length = 150,null=True, blank=True)
    link_expired = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'feedback_link_validation'
        

class VendorFeedback(BaseModel):
    report_check = models.ForeignKey(report_check, on_delete=models.DO_NOTHING, null=False, blank=False, related_name='report_feedback_set')
    overall_feddback = models.IntegerField(null=True,blank=True)
    aditional_feedback = models.TextField(null=True,blank=True)
    status = models.BooleanField(default=True)
    
    
    class Meta:
        db_table = 'vendor_feedback'
    
