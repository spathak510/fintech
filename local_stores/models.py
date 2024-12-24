from django.db import models
import datetime


class BaseModel(models.Model):
    """Base ORM model"""
    # created and updated at date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # meta class
    class Meta:
        abstract = True

    # Time elapsed since creation
    def get_seconds_since_creation(self):
        """
        Find how much time has been elapsed since creation, in seconds.
        This function is timezone agnostic, meaning this will work even if
        you have specified a timezone.
        """
        return (datetime.datetime.utcnow() -
                self.created_at.replace(tzinfo=None)).seconds

class LandingPageUser(BaseModel):
    name = models.CharField(max_length=255, null=True,blank=True)
    mobile_no = models.CharField(max_length=50,null=False,blank=False)
    notification_status = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'landing_page_user'
        
        
        
      
        
class StoresModel(BaseModel):
    parent_id = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=255,null=True,blank=True)
    mobile_num = models.CharField(max_length=50,null=False,blank=False)
    email = models.EmailField(max_length=254, null=True, blank=True)
    branch_name = models.CharField(max_length=255,null=True,blank=True)
    address = models.TextField(null=True,blank=True)
    is_active = models.BooleanField(null=True,blank=True)
    password = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'stores_model'
        

class StoresCardMapping(BaseModel):
    stores_id = models.ForeignKey(StoresModel, on_delete=models.CASCADE, null=False, blank=False, related_name='stores_card_set')
    client_name = models.CharField(max_length=255,null=True,blank=True)
    client_mobile_num = models.CharField(max_length=50,null=False,blank=False)
    servise_type = models.CharField(max_length=255,null=True,blank=True)
    payment = models.BooleanField(null=True,blank=True)
    status = models.BooleanField(null=True,blank=True)
    
    class Meta:
        db_table = 'stores_card_mapping'        
        
        
        
class StoresModelPackageMapping(BaseModel):
    stores_model = models.ForeignKey(StoresModel, on_delete=models.CASCADE, null=False, blank=False, related_name='storeg_model_package_mapping_Set')
    packege_name = models.CharField(max_length=255,null=True,blank=True)
    package_quantity = models.IntegerField(null=True,blank=True)
    status = models.BooleanField(null=True,blank=True)
    
    class Meta:
        db_table = 'stores_model_package_mapping'        
                   
        
    
class NavigantUsersDetail(BaseModel):
    customer_info = models.ForeignKey(to='hv_whatsapp_api.customer_info',on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=255,null=True,blank=True)
    mobile_num = models.CharField(max_length=50,null=False,blank=False)
    email = models.EmailField(null=True,blank=True)
    source = models.CharField(max_length=255,null=False,blank=False)
    sub_source = models.CharField(max_length=255,null=True,blank=True)
    price = models.FloatField(null=True)
    card = models.CharField(max_length=255,null=False,blank=False)
    shared_redeempin = models.CharField(max_length=100,null=True,blank=True)
    is_redeempin_redeemed = models.BooleanField(default=None, null=True)
    is_invite_sent_to_candidate = models.BooleanField(default=None, null=True)
    is_process_completed_by_candidate = models.BooleanField(default=None, null=True)
    is_report_share_to_client = models.BooleanField(default=None, null=True)
    remark = models.TextField(null=True,blank=True)
    
    class Meta:
        db_table = 'navigant_users_detail'
        
        
        
class PartnerUsersDetail(BaseModel):
    customer_info = models.ForeignKey(to='hv_whatsapp_api.customer_info',on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=255,null=True,blank=True)
    mobile_num = models.CharField(max_length=50,null=False,blank=False)
    email = models.EmailField(null=True,blank=True)
    source = models.CharField(max_length=255,null=False,blank=False)
    sub_source = models.CharField(max_length=255,null=True,blank=True)
    price = models.FloatField(null=True)
    card = models.CharField(max_length=255,null=False,blank=False)
    shared_redeempin = models.CharField(max_length=100,null=True,blank=True)
    is_redeempin_redeemed = models.BooleanField(default=None, null=True)
    is_invite_sent_to_candidate = models.BooleanField(default=None, null=True)
    is_process_completed_by_candidate = models.BooleanField(default=None, null=True)
    is_report_share_to_client = models.BooleanField(default=None, null=True)
    remark = models.TextField(null=True,blank=True)
    
    class Meta:
        db_table = 'partner_users_detail'        
    