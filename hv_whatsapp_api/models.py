from __future__ import unicode_literals
from datetime import datetime
from choicesenum import ChoicesEnum
from django.db import models
from django.db import connection
from django.db.models.deletion import DO_NOTHING
# from django.db.models.deletion import models.CASCADE
from .models_core import ChoiceEnum, ModelBase, TrackableModel, StandardResultsSetPagination, RoundingDecimalModelField, FirstQuerySet, ManagerWithFirstQuery, RecordStatus, EmptyModelWithSeqAndStatus, TrackableModelWithSeqAndStatus, EmptyModelBase, EmptyModel, BaseAuditHistory,BaseQuestionSet
import secrets
from django.db.models.signals import post_save
from local_stores.models import StoresModel


class Dummy(models.Model):
    dummy = models.CharField(max_length=1, default='')

class Dashboard(models.Model):
    file_name = models.CharField(max_length=50, default='')

    def __str__(self):
        return self.file_name


class ps_color_code(ChoicesEnum):
    none = '0'
    green = '1'
    red = '2'
    orange = '3'
    yellow = '4'
    gray = '5'
    positive = '6'
    negative = '7'

class check_types(ChoicesEnum):
    none = '0'
    id_check = '1'
    crime_check = '2'
    emp_check = '3'
    kyc_check = '4'
    id_crime_check = '5'
    id_emp_check = '6'
    id_kyc_check = '7'
    crime_emp_check = '8'
    crime_kyc_check = '9'
    emp_kyc_check = '10'
    id_crime_emp_check = '11'
    id_crime_emp_kyc_check = '12'
    id_badge = '13'

class ops_trackable_model(EmptyModel):
    created_at = models.DateTimeField(auto_now_add=True, null=True, editable=False) 
    updated_at = models.DateTimeField(auto_now=True, null=True, editable=False) 
    
    class Meta:
        abstract = True

#---------------------------------whatsapp_models--------------------
class results(ChoicesEnum):
    session_expired = 0
    reminder = 1
    imageOk = 2
    blur_or_Incorrect_image = 3
    father_name_found = 4
    father_name_not_found = 5
    address_allowed = 6
    address_not_allowed = 7
    payment_success = 8
    payment_fail = 9
    otp_correct = 10
    otp_incorrect = 11
    father_name_correct = 12  
    father_name_incorrect = 13
    consent_yes = 14  
    consent_no = 15  
    uan_correct = 16  # correct length for UAN 
    uan_incorrect = 17  # incorrect length for UAN 
    correct_input = 18
    incorrect_input = 19
    valid_coupon = 20
    invalid_coupon = 21
    blocked_user = 22
    invalid_selfie = 23
    skip_customer_type = 24
    skip_customer_type_someone = 25
    gift_card_valid_799 = 26
    gift_card_valid_1499 = 27
    gift_card_invalid = 28
    gift_card_expired = 29
    gift_card_insuf_balance = 30

class action_on_ques(ChoicesEnum):
    save_language_type = 0
    save_service_type = 1
    save_id_type = 2
    go_to_previous_ques = 3
    parse_front_image = 4
    parse_back_image = 5
    save_address = 6
    ask_correct_address = 7
    save_fathername = 8    
    save_UAN = 9
    match_otp = 10  #delete otp fron action on ques and result
    resend_otp = 11
    payment_status_check = 12
    save_customer_type = 13
    check_address_similarity = 14
    check_fathername_similarity = 15 
    save_candidate_mobile_no = 16
    varification_done = 17
    save_consent = 18
    ask_correct_fathername = 19
    save_name = 20
    validate_coupon = 21
    kyc_check = 22
    save_badge_selfie = 23
    get_map_location = 24
    match_uan_otp = 25
    validate_promocode = 26
    validate_gift_card = 27
    redeem_gift_card = 28


class status(ChoicesEnum):
    mobile_unverified = 0
    mobile_verified = 1
    payment_not_recieved = 2
    payment_recieved = 3
    

class report_status(ChoicesEnum):
    pending = '0'
    generated = '1'
    delivered = '2'

class edu_doc_status(ChoiceEnum):
    Pending = '0'
    Completed = '1'
    WIP = '2'
    Insuff_10th = '3'
    Insuff_12th = '4'
    Insuff_10th_12th = '5'
    Rejected = '6'
    Incorrect_number = '7'
    Discrepancy = '8'

class nobroker_package_name(ChoiceEnum):
    Verify_Nanny = '21'
    Verify_Driver = '22'
    Verify_Anyone = '23'
    Verify_Domestic_Help_or_Security_guard = '24'
    Know_the_Identity = '25'

class customer_type(ChoicesEnum):  #updated
    
    customer = '1'
    vendor = '2'
    candidate = '3'

class id_type(ChoicesEnum):
    
    aadhaar = '1'
    driving_licence = '2'
    voter = '3'
    pan = '4'


class remider_count(ChoicesEnum):
    
    min_10 = 0  #after payment ques
    min_20 = 1
    hr_24 = 2
    hr_48 = 3
    hr_71 = 4

class language(ChoicesEnum):
    english = '1'
    hindi = '2'
    
class question_master(models.Model):
    question_id = models.IntegerField(primary_key= True)
    question_desc_eng = models.TextField(default='--')
    question_desc_hindi = models.TextField(default='--')
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return str(self.question_id)+": "+self.question_desc_eng


class communication_myself(models.Model):
    service_type_id = models.IntegerField()
    prev_question_id = models.IntegerField()
    next_question_id = models.IntegerField()
    user_action = models.IntegerField(null=True)
    results = models.CharField(max_length=5, choices=results.choices(), null=True)
    action_on_ques = models.CharField(max_length=5, choices=action_on_ques.choices())


class communication_someoneelse(models.Model):
    service_type_id = models.IntegerField()
    prev_question_id = models.IntegerField()
    next_question_id = models.IntegerField()
    user_action = models.IntegerField(null=True)
    results = models.CharField(max_length=5, choices=results.choices(), null=True)
    action_on_ques = models.CharField(max_length=5, choices=action_on_ques.choices())


class service_detail(models.Model):
    customer_type = models.CharField(max_length=5, choices=customer_type.choices(), editable=False)
    service_type_id = models.IntegerField(default=0)
    service_type_name = models.CharField(max_length=200)
    service_type_name_hindi = models.CharField(max_length=200)
    service_type_price = models.FloatField(null = True)
    final_price_in_words = models.CharField(max_length=200, null=True)
    igst_amount = models.FloatField(null = True)
    igst_percentage = models.FloatField(null = True)
    service_type_discount = models.FloatField(null = True)
    service_type_discount_percentage = models.FloatField(null = True)
    final_price = models.FloatField(null = True)
    check_types = models.CharField(max_length=5, default=0, choices=check_types.choices())

class customer_register(ops_trackable_model):  #save when customer start the communication
    mobile_no = models.CharField(max_length = 20, primary_key = True)
    email_id = models.EmailField(null=True, blank=True)
    mobile_verified = models.BooleanField(default=False)
    customer_type = models.CharField(max_length = 5, default=1, choices=customer_type.choices(), editable=False)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.mobile_no

    
class customer_info(ops_trackable_model):  #save confirmed detail during particular session
    session_id = models.AutoField(primary_key = True)
    customer_type = models.CharField(max_length=5, default=1, choices=customer_type.choices(), blank=True, editable=False)
    service_type_id = models.IntegerField(default=0, null=True, blank=True)
    name = models.CharField(max_length=50, blank=True)
    father_name = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    dob = models.DateField(null=True, blank=True)
    mobile_no = models.CharField(max_length=20)
    adhaar_number = models.CharField(max_length=20, blank=True)
    dl_number = models.CharField(max_length=20, blank=True)
    uan = models.CharField(max_length=20, blank=True)
    mobile_otp = models.IntegerField(null=True, blank=True)
    mobile_verified = models.BooleanField(default = False, null=True, blank=True)
    payment_status = models.BooleanField(default = False, null=True, blank=True)
    final_price = models.FloatField(null=True, blank=True) #final price after promocode or customer skip the promocode
    language_type = models.IntegerField(default=1, null=True, blank=True) 
    id_type = models.CharField(max_length=5, choices=id_type.choices(), blank=True, editable=False)
    customer_gstin = models.CharField(max_length=100, blank=True)
    customer_gst_address = models.CharField(max_length=300, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    selfie_url = models.URLField(max_length=500, null=True, blank=True)
    
    gift_card = models.CharField(max_length=50, blank=True,null=True)
    gift_card_pin = models.CharField(max_length=20, blank=True,null=True)
    gift_card_balance = models.FloatField(null=True, blank=True)
    promo_applied = models.CharField(max_length=20, null=True, blank=True, default = '--')
    aadhaar_client_id = models.CharField(max_length=255,null=True,blank=True)
    aadhaar_verification_response = models.TextField(null=True,blank=True)

    def __str__(self):
        return str(self.session_id)

class qc_auth_tokens(ops_trackable_model):    
    auth_token = models.TextField(blank=False,null=False)


class qc_api_log(ops_trackable_model):    
    customer_info = models.ForeignKey(customer_info, on_delete=models.SET_NULL,null=True,blank=True)
    mob_no = models.CharField(max_length=20, blank=True,null=True)
    url = models.CharField(max_length=500, blank=True,null=True)
    response = models.TextField(blank=True,null=True)
    request_payload = models.TextField(blank=True,null=True)
    headers = models.TextField(blank=True,null=True)
    def save(self, *args, **kwargs):
        if self.customer_info and not self.mob_no:
            self.mob_no = str(self.customer_info.mobile_no)
        super(qc_api_log, self).save(*args, **kwargs)   

class session_map(ops_trackable_model):    
    customer_info = models.ForeignKey(customer_info, on_delete=models.CASCADE)
    mobile_no = models.CharField(max_length = 20)
    url_id = models.CharField(max_length = 100, null=True)
    expire_url = models.BooleanField(default=True, null=True)
    service_type_id = models.IntegerField(default=0, null=True)
    def __str__(self):
        return str(self.customer_info.session_id)
        
class session_log(ops_trackable_model):
    customer_info = models.ForeignKey(customer_info, on_delete=models.CASCADE)
    prev_question_id = models.IntegerField(null=True)
    user_action = models.CharField(max_length=200, null=True, blank=True)
    results = models.CharField(max_length=5, choices=results.choices(), editable=False)
    customer_type = models.CharField(max_length=5, default=1, choices=customer_type.choices())
    language_type = models.IntegerField(default=1, null=True) #True for english  
    service_type_id = models.IntegerField(default=0, null=True)  # set service type_id 0 default
    mobile_no = models.CharField(max_length=20)  #add this also
    id_type = models.CharField(max_length=5, choices=id_type.choices(), blank=True)

    def __str__(self):
        return str(self.customer_info.session_id)


class customer_lookup(ops_trackable_model):
    customer_info = models.ForeignKey(customer_info, on_delete=models.CASCADE)
    vendor_mobile = models.CharField(max_length=20)  # vendor mobile number
    vendor_id = models.IntegerField(null=True)
    candidate_mobile = models.CharField(max_length=20) # someone else mobile number
    service_type_id = models.IntegerField(default=0, null=True)
    vendor_name = models.CharField(max_length=100)
    candidate_name = models.CharField(max_length=100)
    
    def __str__(self):
        return str(self.customer_info.session_id)

class ocr_response(ops_trackable_model):  #parent sessionlog
    customer_info = models.ForeignKey(customer_info, related_name="ocr_set_customer", on_delete=models.CASCADE)
    id_type = models.CharField(max_length=5, choices=id_type.choices())
    front_image_url = models.URLField()
    back_image_url = models.URLField(null= True)
    front_response_str = models.TextField()
    back_response_str = models.TextField()
    front_parse_result = models.TextField()
    back_parse_result = models.TextField()

class kyc_report_data(ops_trackable_model):
    customer_info = models.ForeignKey(customer_info, on_delete=models.CASCADE)
    selfie_url = models.URLField(max_length = 500, null = True)    
    gate_url = models.URLField(max_length = 500, null = True)
    vehicle_or_sign_url = models.URLField(max_length = 500, null = True, default='')
    front_img_url = models.URLField(max_length = 500, null = True)
    back_img_url = models.URLField(max_length = 500, null = True)
    location_img_url = models.URLField(max_length = 500, null = True)
    actual_lat_long = models.CharField(max_length=50)
    claimed_lat_long = models.CharField(max_length=50)
    current_address = models.TextField()
    stay_from = models.DateField(null=True, blank=True)
    stay_to = models.DateField(null=True, blank=True)
    ownership_status = models.CharField(max_length=50)
    
    def __str__(self):
        return str(self.customer_info.session_id)

# class kyc_artifacts(models.Model):
#     customer_type = models.CharField(max_length=5, choices=customer_type.choices())
#     service_type_id = models.IntegerField(default=0)
#     img1_msg = models.CharField(max_length=100)
#     img2_msg = models.CharField(max_length=100)
#     img3_msg = models.CharField(max_length=100)
#     img4_msg = models.CharField(max_length=100)
#     img5_msg = models.CharField(max_length=100)
#     img6_msg = models.CharField(max_length=100)
    
class order(ops_trackable_model):
    customer_info = models.ForeignKey(customer_info, related_name="order_set_customer", null=True, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200,default='-')
    price = models.FloatField(null=True)
    payment_recieved_date = models.DateTimeField(auto_now_add=True, null = True)
    transaction_id = models.CharField(max_length=200,default='-')
    mobile_no = models.CharField(max_length=20)
    auto_or_manual = models.CharField(max_length=20, default='-')
    final_status = models.CharField(max_length=20, default='-')
    report_sent_time = models.DateTimeField(max_length=20, blank=True, null=True)
    send_incomplete_report = models.BooleanField(null=True, default=False)
    report_url = models.URLField(null= True)

class consent(models.Model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20)
    consent_time = models.DateTimeField(auto_now_add=True)


class transaction_log(ops_trackable_model):
    customer_info = models.ForeignKey(customer_info, on_delete=models.CASCADE, null=True)
    transaction_id = models.CharField(max_length=200)
    fetch_str = models.TextField()
    capture_str = models.TextField()
    authorised = models.BooleanField(default=False)
    captured = models.BooleanField(default=False)

    def __str__(self):
        return self.transaction_id


class reminder(ops_trackable_model):
    customer_info = models.ForeignKey(customer_info, on_delete=models.CASCADE)
    reminder_type = models.BooleanField(null=True)
    reminder_counter = models.CharField(max_length=5, default=0, choices=remider_count.choices())
    minutes_verification = models.IntegerField(null=True)
    status = models.CharField(max_length=5, default=0, choices=status.choices())
    mobile_no = models.CharField(max_length=20)

    def __str__(self):
        return str(self.customer_info.session_id)

class criminal_result(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    request_sent =  models.TextField()
    api_result = models.TextField()
    api_result_for_report = models.TextField()  #use for report purpose
    rule_engine_result = models.TextField()
    is_check_passed = models.BooleanField()
    color_code = models.CharField(max_length=5, default=0, choices = ps_color_code.choices())
    manual_response = models.TextField(default='') ## for criminal check red cases
    manual_color_code = models.CharField(max_length=5, default=0, choices = ps_color_code.choices())
    remark = models.TextField()
    check_id = models.CharField(max_length=50)
    sent_for_manual = models.BooleanField(default=False)

    def __str__(self):
        return self.order.order_id

class criminal_result_external(ops_trackable_model):
    order_id = models.CharField(max_length=50, primary_key=True)
    search_term_json =  models.TextField(editable=False)
    crime_api_result = models.TextField(editable=False)
    rule_engine_result = models.TextField(editable=False)
    claimed_details = models.TextField(default='')
    is_check_passed = models.BooleanField(editable=False)
    color_code = models.CharField(max_length=5, default=0, choices = ps_color_code.choices(), editable=False)
    manual_color_code = models.CharField(max_length=5, default=0, choices = ps_color_code.choices(), editable=False)
    sent_for_manual = models.BooleanField(default=False, editable=False)
    source_name = models.CharField(max_length=50, editable=False)
    prob_status = models.CharField(max_length=50, editable=False)
    final_result_json = models.TextField(editable=False)

    def __str__(self):
        return self.order_id

class uan_api_key(ops_trackable_model):
    apiKey = models.CharField(max_length=500)


class uan_result(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    uan_api_result = models.TextField()
    rule_engine_result = models.TextField()
    is_check_passed = models.BooleanField(default=False)
    color_code = models.CharField(max_length=5, default=0, choices = ps_color_code.choices())
    org_details = models.TextField()

    def __str__(self):
        return self.order.order_id


class aadhaar_manual(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    uid_data =  models.TextField()

    def __str__(self):
        return self.order.order_id


class dl_result(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    request_sent =  models.TextField()
    api_result = models.TextField()
    api_result_for_report = models.TextField()
    rule_engine_result = models.TextField()
    is_check_passed = models.BooleanField()
    color_code = models.CharField(max_length=5, default=0, choices = ps_color_code.choices())
    manual_response = models.TextField() ## for dl no karza response
    manual_color_code = models.CharField(max_length=5, default=0, choices = ps_color_code.choices())
    remark = models.TextField()

    def __str__(self):
        return self.order.order_id

class adhaar_result(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    request_sent =  models.TextField()
    api_result = models.TextField()
    api_result_for_report = models.TextField(editable=False)
    rule_engine_result = models.TextField()
    is_check_passed = models.BooleanField()
    color_code = models.CharField(max_length=5, default=0, choices = ps_color_code.choices())
    
    def __str__(self):
        return self.order.order_id
  
class report(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    report_json = models.TextField()
    
    def __str__(self):
        return self.order.order_id


# Model for report and check status
class report_check(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    report_status = models.CharField(max_length=5, choices=report_status.choices(), default=0)
    id_check_status = models.BooleanField(null = True)
    crime_check_status = models.BooleanField(null = True)
    emp_check_status = models.BooleanField(null = True, editable=False)
    send_mail_for_manual_check = models.BooleanField(null = True, default=False, editable=False)
    send_review_mail = models.BooleanField(null = True, default=False)
    send_report = models.BooleanField(null = True, default=False)
    init_qc_done = models.BooleanField(default=False)


class dl_manual_response(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    front_dl_image = models.URLField(max_length=200, blank = True, null = True)
    back_dl_image = models.URLField(max_length=200, blank = True, null = True)
    dl_number = models.CharField(max_length=200, help_text="Input DL Number")
    name = models.CharField(max_length=200, help_text="Input Name")
    father_name = models.CharField(max_length=200, help_text="Input Father name")
    address = models.TextField(help_text="Input Address")
    issue_date = models.CharField(max_length=200, help_text="Input date as DD-MM-YYYY")

    def __str__(self):
        return self.order.order_id

class api_hit_count(ops_trackable_model):
    order = models.ForeignKey(order, on_delete=models.CASCADE)
    anti_captcha = models.IntegerField(default=0)
    dl_api = models.IntegerField(default=0)
    crime_api = models.IntegerField(default=0)
    emp_api = models.IntegerField(default=0)
    address_parser_api = models.IntegerField(default=0)


class url_expiry(ops_trackable_model): #model for url expiry
    customer_info = models.ForeignKey(customer_info, on_delete=models.CASCADE)
    url_id = models.CharField(max_length=100, primary_key=True)
    url_send_time = models.DateTimeField(auto_now=True)
    expired = models.BooleanField(default=False)

class customer_coupon_code(ops_trackable_model):
    mobile_no = models.CharField(max_length=20, primary_key=True)
    allowed_attempt =  models.IntegerField(default = 3)
    last_attempt_time = models.DateTimeField()
    allowed = models.BooleanField(default=True)

    def __str__(self):
        return self.mobile_no

class customer_promocode(ops_trackable_model):
    mobile_no = models.CharField(max_length=20, primary_key=True)
    allowed_attempt =  models.IntegerField(default = 3)
    last_attempt_time = models.DateTimeField()
    allowed = models.BooleanField(default=True)

    def __str__(self):
        return self.mobile_no


class Gift(models.Model):
    mobile_number = models.CharField(max_length=200, null = True)
    
    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        """
        Connected to the post_save signal of the UniqueCodes model. This is used to set the
        code once we have created the db instance and have access to the primary key (ID Field)
        """
        # If new database record
        if created:
            # We have the primary key (ID Field) now so let's grab it
            id_string = str(instance.id)
            # Define our random string alphabet (notice I've omitted I,O,etc. as they can be confused for other characters)
            upper_alpha = "ABCDEFGHJKLMNPQRSTVWXYZ123456789"
            # Create an 8 char random string from our alphabet
            random_str = "".join(secrets.choice(upper_alpha) for i in range(6))
            # Append the ID to the end of the random string
            instance.code = (random_str + id_string)
            # Save the class instance
            instance.save()

class UniqueCodes(models.Model):
    """
    Class to create human friendly gift/coupon codes.
    """
    # Model field for our unique code
    id = models.AutoField(primary_key=True)
    customer_info = models.ForeignKey(customer_info, on_delete=models.SET_NULL, null=True)
    is_redeemed = models.BooleanField(default=False)
    service_type_id = models.IntegerField(default=0)
    code = models.CharField(max_length=20)
    code_type = models.CharField(max_length=20)
    mobile_no = models.CharField(max_length=20, null = True)
    redeem_time = models.DateTimeField(null=True)
    assigned_to = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=50, default='')
    is_distributed = models.BooleanField(default=False)
    # partner_id = models.ForeignKey(StoresModel, on_delete=models.DO_NOTHING, null=True,blank=True)

    def __str__(self):
        return "%s" % (self.code,)


class PromoCodes(models.Model):
    """
    Class to create human friendly gift/coupon codes.
    """

    # Model field for our unique code
    customer_info = models.ForeignKey(customer_info, on_delete=models.SET_NULL, null = True)
    is_redeemed = models.BooleanField(default=False)
    code = models.CharField(max_length=20, primary_key=True)
    mobile_no = models.CharField(max_length=20)
    redeem_time = models.DateTimeField(null=True) #date time when code is redeem
    dispatch_time = models.DateTimeField(null=True) #date time when we share codes with internal team
    assigned_to = models.CharField(max_length=50, default='NA')
    is_distributed = models.BooleanField(default=False)
    discount_percentage = models.IntegerField()

    def __str__(self):
        return "%s" % (self.code,)

class GeneralPromoCodes(models.Model):
    """
    Class to create human friendly gift/coupon codes.
    """
    code = models.CharField(max_length=20, primary_key=True)
    assigned_to = models.CharField(max_length=50, default='NA')
    is_expired = models.BooleanField(default=False)
    discount_percentage = models.IntegerField()

    def __str__(self):
        return "%s" % (self.code,)


# Connect the post_create function to the UniqueCodes post_save signal
post_save.connect(Gift.post_create, sender=UniqueCodes)

# class send_reminder(ops_trackable_model):
#     mobile_number = models.CharField(max_length=20)
#     name = models.CharField(max_length=100)
#     email_id = models.EmailField(null=True)
#     city = models.CharField(max_length=100)
#     type_of_check = models.CharField(max_length=100)
#     followup_status = models.BooleanField(default=False)


class AdminIncompleteTransactionModel(models.Model):
    customer_info = models.ForeignKey(customer_info, on_delete=models.SET_NULL, null=True, blank=True)
    mobile_no = models.CharField(max_length=20)
    starts_with = models.CharField(max_length=20, default='--')
    language_selected = models.CharField(max_length=20, default='--')
    customer_type = models.CharField(max_length=20, default='--')
    package_name = models.CharField(max_length=100, default='--')
    id_uploaded = models.CharField(max_length=20, default='--') # Using this field just to show id upload status    
    promo_applied = models.CharField(max_length=20, default='--')
    last_message_time = models.DateTimeField(auto_now=True)
    payment_link_status = models.CharField(max_length=20, default='Not Sent')
    followup_status = models.BooleanField(default=False)

class EducationData(ops_trackable_model):
    unique_id = models.CharField(max_length=50)
    mobile_no = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    tenth_url = models.URLField(null= True, editable=False)
    twelveth_url = models.URLField(null= True, editable=False)
    extra_urls = models.TextField(default='-', editable=False)
    doc_reminder = models.IntegerField(default=2)
    insuff_reminder = models.IntegerField(default=3)
    language = models.CharField(max_length=50, editable=False)
    tenth = models.CharField(max_length=50, default='Yes', editable=False)
    twelveth = models.CharField(max_length=50, default='No')
    message_sent = models.BooleanField(default=False)
    case_status = models.CharField(max_length=5, choices=edu_doc_status.choices(), default='0')
    case_id = models.CharField(max_length=50, blank=True)
    insuff_10th_remark = models.TextField(blank=True, help_text="Enter 10th Insuff Remark, if any")
    insuff_12th_remark = models.TextField(blank=True, help_text="Enter 12th Insuff Remark, if any")
    insuff_time = models.DateTimeField(null=True, editable=False)
    insuff_oni_update = models.BooleanField(default=False, editable=False)
    last_message_sid = models.CharField(max_length=100, default='', blank=True, editable=False)
    msg_status = models.CharField(max_length=100, default='--')
    hide_record = models.BooleanField(default=False)
    
    def __init__(self, *args, **kwargs):
        super(EducationData, self).__init__(*args, **kwargs)
        self.old_case_status = self.case_status
    
    def save(self, *args, **kwargs):
        mobile_no = (self.mobile_no).strip()
        if len(mobile_no) == 10:
            self.mobile_no = '+91' + mobile_no
        elif len(mobile_no) == 12:
            self.mobile_no = '+' + mobile_no
        if self.old_case_status != self.case_status: # if insufficiency raised
            self.insuff_reminder = 3
            self.insuff_time = datetime.now()
            if (self.case_status == '3' or self.case_status == '5') and self.tenth_url:
                if len(self.extra_urls) > 10:
                    self.extra_urls = self.extra_urls + ',' + self.tenth_url
                    self.tenth_url = None
                else:
                    self.extra_urls = self.tenth_url
                    self.tenth_url = None
            if (self.case_status == '4' or self.case_status == '5') and self.twelveth_url:
                if len(self.extra_urls) > 10:
                    self.extra_urls = self.extra_urls + ',' + self.twelveth_url
                    self.twelveth_url = None
                else:
                    self.extra_urls = self.twelveth_url
                    self.twelveth_url = None
        super(EducationData, self).save(*args, **kwargs)


class LatLong(ops_trackable_model):
    request_id = models.CharField(max_length=100)
    claimed_address = models.TextField(null=True, blank=True)
    mobile_no = models.CharField(max_length=100, null=True, blank=True)
    candidate_name = models.CharField(max_length=100, null=True, blank=True)
    claimed_lat_long = models.TextField(null=True, blank=True)
    location_json = models.TextField(null=True, blank=True)
    actual_lat_long = models.CharField(max_length=100, null=True, blank=True)
    distance = models.IntegerField(null=True, blank=True)
    is_match = models.BooleanField(null=True, blank=True)
    browser_name = models.CharField(max_length=100, null=True, blank=True)
    operating_system = models.CharField(max_length=100, null=True, blank=True)
    browser_version = models.CharField(max_length=100, null=True, blank=True)
    nearest_landmark = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.request_id

class CowinData(ops_trackable_model):
    check_id = models.CharField(max_length=50)
    whatsapp_mobile_no = models.CharField(max_length=20)
    name = models.CharField(max_length=50)
    birth_year = models.CharField(max_length=10)
    email_id = models.EmailField(null=True, blank=True)
    client_name = models.CharField(max_length=50, blank=True, default='Demo')
    case_status = models.BooleanField(default=False, editable=False) #False -> pending, True->Completed
    cowin_mobile_no = models.CharField(max_length=20, blank=True, editable=False)
    cowin_otp = models.CharField(max_length=10, editable=False)
    father_name = models.CharField(max_length=50, blank=True, editable=False)
    vaccination_status = models.CharField(max_length=50, default='--', blank=True, editable=False)
    api_result = models.TextField(blank=True, editable=False)
    report_json = models.TextField(blank=True, editable=False)
    report_url = models.URLField(null= True, blank=True, editable=False)
    reminder_count = models.IntegerField(default=3, blank=True, editable=False)
    last_message_sid = models.CharField(max_length=100, default='', blank=True, editable=False)
    msg_status = models.CharField(max_length=100, default='--', blank=True, editable=False)
    hide_record = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        whatsapp_mobile_no = (str(self.whatsapp_mobile_no)).strip()
        if len(whatsapp_mobile_no) == 10:
            self.whatsapp_mobile_no = '+91' + str(self.whatsapp_mobile_no)
        elif len(whatsapp_mobile_no) == 12:
            self.whatsapp_mobile_no = '+' + str(self.whatsapp_mobile_no)        
        super(CowinData, self).save(*args, **kwargs)


class NobrokerOrder(ops_trackable_model):
    order_id = models.CharField(max_length=50)
    applicant_name = models.CharField(max_length=200)
    package = models.CharField(max_length=5, choices=nobroker_package_name.choices())
    mobile_no = models.CharField(max_length=20)
    email_id = models.EmailField()
    sms_content = models.TextField(editable=False)
    whatsapp_content = models.TextField(editable=False)
    email_content = models.TextField(editable=False)

    def save(self, *args, **kwargs):
        mobile_no = (str(self.mobile_no)).strip()
        if len(mobile_no) == 10:
            self.mobile_no = '+91' + str(self.mobile_no)
        elif len(mobile_no) == 12:
            self.mobile_no = '+' + str(self.mobile_no)        
        super(NobrokerOrder, self).save(*args, **kwargs)

    def __str__(self):
        return self.order_id

class EmailTemplate(models.Model):
    template_name = models.CharField(max_length=100)
    email_html = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.template_name

class VerifyNow(ops_trackable_model):
    service_detail = models.ForeignKey(service_detail, on_delete=DO_NOTHING, null=True)
    mobile_no = models.CharField(max_length=20)
    email = models.EmailField(null=True)
    service_type_id = models.IntegerField(default=0)
    transaction_id = models.CharField(max_length=200)
    transaction_captured = models.BooleanField(default=False)
    redemption_pin = models.CharField(max_length=30)
    is_redemption_pin_shared = models.BooleanField(default=False)
    is_session_expired = models.BooleanField(default=False)
    transaction_detail = models.TextField(null=True)
    short_url = models.URLField(null=True)
    razorpay_payment_link_id = models.CharField(max_length=50)
    razorpay_payment_link_status = models.CharField(max_length=50)
    invoice_json = models.TextField()
    discount = models.IntegerField(default=0)
    # promo_code = models.ForeignKey(GeneralPromoCodes, on_delete=DO_NOTHING, null=True,blank=True)
    is_active = models.BooleanField(default=True)


class VisaBankDetail(ops_trackable_model):
    bank_name = models.CharField(max_length=100, null=True)
    request_id = models.CharField(max_length=100, null=True)


# SSL check details model with file storage path
def set_selfie_path(instance, filename):
    file_path = "sslcheck_selfie/" + str(instance.customer_info_id)+"_" + filename
    return file_path

def set_signature_path(instance, filename):
    file_path = "sslcheck_signature/" + str(instance.customer_info_id)+"_" + filename
    return file_path    

def set_location_map_path(instance, filename):
    file_path = "sslcheck_map/" + str(instance.customer_info_id)+"_" + "map.png"
    return file_path
class SSLChekDetails(ops_trackable_model):
    customer_info = models.ForeignKey(customer_info, on_delete=models.CASCADE)
    selfie_url = models.FileField(upload_to=set_selfie_path, null=True, blank=True)    
    signature_url = models.FileField(upload_to=set_signature_path, null=True, blank=True)
    location_img_url = models.FileField(upload_to=set_location_map_path, null=True, blank=True)    