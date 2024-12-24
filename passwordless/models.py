from django.db import models

# Create your models here.
class ops_trackable_model(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, editable=False) 
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=False) 
    
    class Meta:
        abstract = True

class MagicLink(ops_trackable_model):
    email = models.EmailField(null=True)
    mobile_no = models.CharField(max_length=20)
    url_token = models.CharField(max_length=250)
    sec_token = models.CharField(max_length=250, default='')
    is_active = models.BooleanField(null=True)
    
    def __str__(self):
        return self.request_id