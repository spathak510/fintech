from django.db import models

class ExternalApiBasemodel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, editable=False) 
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=False) 
    
    class Meta:
        abstract = True

class GstVerification(ExternalApiBasemodel):
    gst_number = models.CharField(null=False, blank=False, max_length=15)
    company_pan_number = models.CharField(null=True, blank=True, max_length=10)
    gst_status = models.CharField(null=False, blank=False, max_length=50)
    last_tax_paid_date = models.CharField(null=False, blank=False, max_length=50)
    raw_response = models.TextField(null=False,blank=False)


    def save(self, *args, **kwargs):
        self.company_pan_number = self.gst_number[2:12]
        super(GstVerification, self).save(*args, **kwargs)

class McaVerification(ExternalApiBasemodel):
    cin_number = models.CharField(null=False, blank=False, max_length=21)
    company_name = models.CharField(null=False, blank=False, max_length=1000)
    status = models.CharField(null=False, blank=False, max_length=50)
    address = models.CharField(null=False, blank=False, max_length=1000)
    industry = models.CharField(null=False, blank=False, max_length=1000)
    incorporation_date = models.DateField(null=False, blank=False)
    directors = models.TextField(null=False ,blank=False)
    raw_response = models.TextField(null=False,blank=False)


    def save(self, *args, **kwargs):
        super(McaVerification, self).save(*args, **kwargs)

class TempFiles(ExternalApiBasemodel):
    file = models.FileField(upload_to='temp-files',null=False,blank=False)
    def save(self, *args, **kwargs):
        super(TempFiles, self).save(*args, **kwargs)

class HitRecord(ExternalApiBasemodel):
    user = models.CharField(max_length=100, null=True, blank=True)
    api_name = models.CharField(max_length=100, null=True, blank=True)
    api_endpoint =  models.CharField(max_length=100, null=True, blank=True)
    hit_time = models.DateTimeField()
    payload = models.TextField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.user)
    
    class Meta:
        db_table = 'hit_record'


def set_initial_doc_path(instance, filename):
    file_path = "doc_tampering_initial_doc/" + str(instance.submission_id)+"_" + filename
    return file_path

def set_tampered_doc_path(instance, filename):
    file_path = "doc_tampering_tampered_doc/" + str(instance.submission_id)+"_" + filename
    return file_path

class DocumentTampering(ExternalApiBasemodel):
    submission_id = models.CharField(max_length=255,null=False,blank=False)
    initial_doc = models.FileField(upload_to=set_initial_doc_path,null=False,blank=False)
    tampered_doc = models.FileField(upload_to=set_tampered_doc_path,null=False,blank=False)
    
    class Meta:
        db_table = 'document_tampering'
    