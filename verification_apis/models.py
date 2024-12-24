from django.db import models
import uuid
# from hv_whatsapp import settings as app_settings


# Create your models here.
class ops_trackable_model(models.Model):
    # create uuid field
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, editable=False) 
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=False) 
    
    class Meta:
        abstract = True

class DrivingLicenseVerification(ops_trackable_model):
    dl_no = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    dob = models.DateField()
    address = models.TextField(blank=True)
    dl_no_match = models.BooleanField(default=True)
    name_match = models.BooleanField(default=False)
    father_name_match = models.BooleanField(default=False)
    dob_match = models.BooleanField(default=True)
    source_api_response = models.TextField(blank=True)
    user = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return str(self.request_id)

class PANVerification(ops_trackable_model):
    pan_no = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, blank=True)
    dob = models.DateField(null=True, blank=True)
    pan_no_match = models.BooleanField(default=True)
    name_match = models.BooleanField(default=False)
    source_api_response = models.TextField(blank=True)
    
    def __str__(self):
        return str(self.request_id)

class PassportVerification(ops_trackable_model):
    passport_no = models.CharField(max_length=50)
    file_no = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    dob = models.DateField()
    father_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    passport_no_match = models.BooleanField(default=False)
    name_match = models.BooleanField(default=False)
    dob_match = models.BooleanField(default=True)
    file_no_match = models.BooleanField(default=True)
    source_api_response = models.TextField(blank=True)
    
    def __str__(self):
        return str(self.request_id)

class VoterIDVerification(ops_trackable_model):
    voter_id_no = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)  
    voter_id_no_match = models.BooleanField(default=True)
    name_match = models.BooleanField(default=False)
    father_name_match = models.BooleanField(default=False)
    dob_match = models.BooleanField(default=False)
    gender_match = models.BooleanField(default=False)
    source_api_response = models.TextField(blank=True)
    user = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return str(self.request_id)

class AadhaarVerification(ops_trackable_model):
    aadhaar_no = models.CharField(max_length=50)
    name = models.CharField(max_length=100, blank=True)
    father_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20)
    dob = models.DateField()
    yob = models.BooleanField(default=False)
    address = models.TextField()
    state = models.CharField(max_length=50, null=True)
    age_range = models.CharField(max_length=20, null=True)
    aadhaar_mobile_no = models.CharField(max_length=20, blank=True)
    aadhaar_no_match = models.BooleanField(default=True)
    gender_match = models.BooleanField(default=False)
    state_match = models.BooleanField(default=False)
    age_match = models.BooleanField(default=False)
    source_api_response = models.TextField(blank=True)
    
    def __str__(self):
        return str(self.request_id)

class CriminalVerification(ops_trackable_model):
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    dob = models.DateField()
    address = models.TextField()
    criminal_case_found = models.BooleanField(default=False)
    rule_engine_result = models.TextField(blank=True)
    source_api_response = models.TextField(blank=True)
    
    def __str__(self):
        return str(self.request_id)