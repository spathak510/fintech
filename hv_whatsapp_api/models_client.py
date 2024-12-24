from __future__ import unicode_literals
import uuid
import datetime
import inspect
import json
from decimal import Decimal
from enum import Enum
from choicesenum import ChoicesEnum
from django.db import models
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from django.db import connection
from .models_core import ChoiceEnum, ModelBase, TrackableModel, StandardResultsSetPagination, RoundingDecimalModelField, FirstQuerySet, ManagerWithFirstQuery, RecordStatus, EmptyModelWithSeqAndStatus, TrackableModelWithSeqAndStatus, EmptyModelBase, EmptyModel, BaseAuditHistory, BaseQuestionSet


class ops_tat_calender_types(ChoicesEnum):
    none = 0
    helloverify = 1
    client_specific = 2
    all_days = 3


class ops_client_master(TrackableModelWithSeqAndStatus):
    client_code = models.CharField(default='', max_length=20, null=True)
    client_id = models.CharField(default='', max_length=20, null=True)
    abbr = models.CharField(default='', max_length=50, null=True)
    name = models.CharField(default='', max_length=100, null=True)
    client_billing_name = models.CharField(default='', max_length=100, null=True)
    address = models.CharField(default='', max_length=20, null=True)
    country = models.CharField(default='', max_length=20, null=True)
    state = models.CharField(default='', max_length=20, null=True)
    city = models.CharField(default='', max_length=20, null=True)
    pin = models.CharField(default='', max_length=20, null=True)
    referred_by = models.CharField(default='', max_length=200, null=True)
    client_logo = models.CharField(default='', max_length=200, null=True)
    client_css = models.CharField(default='', max_length=200, null=True)
    additional_data = models.CharField(default='', max_length=1000, null=True)
    nature_of_business = models.IntegerField(default=0)
    creid_id = models.IntegerField(default=0)
    is_active = models.BooleanField(default=False, null=True)
    group_id = models.IntegerField(default=0)
    billing_type = models.CharField(default='', max_length=50, null=True)
    current_visibility = models.CharField(max_length=100, default='', null=True)
    api_url = models.CharField(max_length=50, default='', null=True)
    themes = models.CharField(max_length=50, default='', null=True)
    is_insuff_expire = models.BooleanField(default=False, null=True)


class ops_client_agreement(TrackableModel):
    id = models.AutoField(primary_key=True)
    client_master_ref = models.ForeignKey(ops_client_master, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True, null=True)
    agreement_version_signed = models.CharField(max_length=1000, default='', null=True)
    is_penalty_clause = models.BooleanField(default=False, null=True)
    penalty_clause_remarks = models.CharField(max_length=2000, default='', null=True)
    agreement_made_on = models.DateField(auto_now_add=True, blank=True, null=True)
    agreement_expired_on = models.DateField(auto_now_add=True, blank=True, null=True)
    agreement_expiry_dt_remarks = models.CharField(max_length=1000, default='', null=True)
    is_insufficiency_billing = models.BooleanField(default=False, null=True)
    case_initiated_with_first_level = models.CharField(max_length=25, default='', null=True)
    billing_cycle = models.CharField(max_length=50, default='', null=True)
    annexure_cycle = models.CharField(max_length=50, default='', null=True)
    price_type = models.IntegerField(default=0, null=True)
    scop_of_work = models.CharField(max_length=25, default='', null=True)
    scop_of_work_remarks = models.CharField(max_length=2000, default='', null=True)
    reverification_cost = models.CharField(max_length=200, default='', null=True)
    extra_cost_approval = models.CharField(max_length=25, default='', null=True)
    intrim_report_required = models.CharField(max_length=25, default='', null=True)
    descripancy_matrix = models.CharField(max_length=100, default='', null=True)
    client_revert_requirement = models.CharField(max_length=100, default='', null=True)
    sla_time = models.CharField(max_length=50, default='', null=True)
    discrepency_matrix = models.CharField(max_length=100, default='', null=True)
    is_mandatory_flag = models.BooleanField(default=False, null=True)
    is_tat_casewise_active = models.BooleanField(default=False, null=True)
    tat_internal_days = models.IntegerField(default=0)
    tat_extenal_days = models.IntegerField(default=0)
    tat_reverification = models.CharField(max_length=25, default='', null=True)
    tat_reverification_remarks = models.CharField(max_length=2000, default='', null=True)
    is_tat_insuff_expire_days = models.BooleanField(default=False, null=True)
    is_tat_client_review = models.BooleanField(default=False, null=True)
    tat_client_review_expire_days = models.CharField(max_length=2000, default='', null=True)
    tat_calender_type = models.CharField(max_length=2, default=0, choices=ops_tat_calender_types.choices(), null=True)
    tat_remarks = models.CharField(max_length=2000, default='', null=True)


class ops_client_billing_info(TrackableModel):
    id = models.AutoField(primary_key=True)
    client_master_ref = models.ForeignKey(ops_client_master, on_delete=models.CASCADE, null=True)
    billing_under = models.CharField(max_length=3, default='HV', null=True)
    master_name = models.CharField(max_length=200, default='', null=True)
    sbu_name = models.CharField(max_length=200, default='', null=True)
    location = models.CharField(max_length=200, default='', null=True)
    credit_period = models.IntegerField(default=30, null=True)
    internal_spoc_name = models.CharField(max_length=200, default='', null=True)
    internal_spoc_email = models.CharField(max_length=200, default='', null=True)
    internal_spoc_phone = models.CharField(max_length=200, default='', null=True)
    annexure_approval_spoc_name = models.CharField(max_length=200, default='', null=True)
    annexure_approval_email = models.CharField(max_length=200, default='', null=True)
    annexure_approval_phone = models.CharField(max_length=200, default='', null=True)
    invoice_approval_spoc_name = models.CharField(max_length=200, default='', null=True)
    invoice_approval_email = models.CharField(max_length=200, default='', null=True)
    invoice_approval_phone = models.CharField(max_length=200, default='', null=True)
    collection_approval_spoc_name = models.CharField(max_length=200, default='', null=True)
    collection_approval_email = models.CharField(max_length=200, default='', null=True)
    collection_approval_phone = models.CharField(max_length=200, default='', null=True)


class ops_client_risk_matrix(TrackableModel):
    id = models.AutoField(primary_key=True)
    client_master_ref = models.ForeignKey(ops_client_master, on_delete=models.CASCADE, null=True)


class ops_client_rules(TrackableModel):
    id = models.AutoField(primary_key=True)
    client_master_ref = models.ForeignKey(ops_client_master, on_delete=models.CASCADE, null=True)


class ops_client_sow(TrackableModel):
    id = models.AutoField(primary_key=True)
    client_master_ref = models.ForeignKey(ops_client_master, on_delete=models.CASCADE, null=True)
