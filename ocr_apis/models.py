import imp
from hv_whatsapp_api.models import status
from django.db import models
from hv_whatsapp_api.models_core import ChoicesEnum 
import uuid
# from hv_whatsapp import settings as app_settings

class report_status(ChoicesEnum):
    pending = '0'
    generated = '1'
    delivered = '2'

# Create your models here.
class ops_trackable_model(models.Model):
    # create uuid field
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, editable=False) 
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=False) 
    
    class Meta:
        abstract = True

# class UploadImageForOCR(models.Model):
#     name = models.CharField(max_length=100)
#     image = models.ImageField(upload_to=app_settings.MEDIA_ROOT+'/ocr_imgs/', blank=True, null=True)

class DrivingLicenseOcrFront(ops_trackable_model):
    ocr_string = models.TextField()
    dl_number = models.CharField(max_length=100)
    name = models.CharField(max_length=100, blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    dob = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return str(self.request_id)

class DrivingLicenseOcrBack(ops_trackable_model):
    ocr_string = models.TextField()
    dl_number = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100, blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    dob = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return str(self.request_id)

class VoterIDOcrFront(ops_trackable_model):
    ocr_string = models.TextField()
    vid = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=100, blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    dob = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return str(self.request_id)

class VoterIDOcrBack(ops_trackable_model):
    ocr_string = models.TextField()
    vid = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    dob = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return str(self.request_id)

class PassportIDOcrFront(ops_trackable_model):
    ocr_string = models.TextField()
    pno = models.CharField(max_length=100)
    name = models.CharField(max_length=100, blank=True)
    dob = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return str(self.request_id)

class PassportIDOcrBack(ops_trackable_model):
    ocr_string = models.TextField()
    fileNo = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    fileNo = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return str(self.request_id)

class AadhaarOcrFront(ops_trackable_model):
    ocr_string = models.TextField()
    adhaar_number = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=100, blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    dob = models.CharField(max_length=20, blank=True)
    yob = models.BooleanField(blank=True, null=True)
    
    def __str__(self):
        return str(self.request_id)

class AadhaarOcrBack(ops_trackable_model):
    ocr_string = models.TextField()
    adhaar_number = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return str(self.request_id)

class PanOcr(ops_trackable_model):
    ocr_string = models.TextField()
    pan_number = models.CharField(max_length=100)
    Name = models.CharField(max_length=100, blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    dob = models.CharField(max_length=100,null=True, blank=True)
    
    def __str__(self):
        return str(self.request_id)

# Model for report and check status
class report_check(ops_trackable_model):
    request_id = models.CharField(max_length=100)
    claimed_data = models.TextField()
    id_check = models.BooleanField(null = True)
    crime_check = models.BooleanField(null = True)
    crime_res = models.TextField()
    emp_check = models.BooleanField(null = True)
    emp_res = models.TextField()
    is_completed = models.BooleanField(default=False)
    retry_count = models.IntegerField(default=2)
    final_res = models.TextField()

