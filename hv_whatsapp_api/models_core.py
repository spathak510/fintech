from __future__ import unicode_literals
import uuid
import datetime
import inspect
from decimal import Decimal
from enum import Enum
from choicesenum import ChoicesEnum

from django.db import models
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from django.db import connection


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        members = inspect.getmembers(cls, lambda m: not(inspect.isroutine(m)))
        props = [m for m in members if not(m[0][:2] == '__')]
        choices = tuple([(str(p[1].value), p[0]) for p in props])
        return choices


def round_decimal(value, places):
    if value is not None:
        return value.quantize(Decimal(10) ** -places)
    return value


class RoundingDecimalModelField(models.DecimalField):
    def to_python(self, value):
        value = super(RoundingDecimalModelField, self).to_python(value)
        return round_decimal(value, self.decimal_places)


class FirstQuerySet(models.query.QuerySet):
    def first(self):
        try:
            return self[0]
        except:
            return None

    def ten(self):
        try:
            return self[:10]
        except:
            return None


class ManagerWithFirstQuery(models.Manager):
    def get_query_set(self):
        return FirstQuerySet(self.model)


class RecordStatus(ChoiceEnum):
    Inactive = 0
    Active = 1
    Deleted = 2


class ModelBase(models.Model):
    # 0 Inactive, 1 Active, 2 Deleted
    record_status = models.CharField(max_length=1, default=1, choices=RecordStatus.choices())
    # models.DateTimeField('date published') default=datetime.datetime.now().date()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField("row created by", max_length=200, default='NA')
    updated_at = models.DateTimeField(auto_now=True)  # models.DateTimeField('date published')
    updated_by = models.CharField("row updated by", max_length=200, default='NA')
    lang = models.CharField("mapped with language_key from Language table", max_length=20, default='en')
    objects = ManagerWithFirstQuery()

    class Meta:
        abstract = True


class EmptyModelBase(models.Model):
    objects = ManagerWithFirstQuery()

    class Meta:
        abstract = True


# ------------------
# base model types
# ------------------
class EmptyModel(models.Model):
    objects = ManagerWithFirstQuery()

    class Meta:
        abstract = True


class EmptyModelWithSeqAndStatus(models.Model):
    objects = ManagerWithFirstQuery()
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    seq = models.IntegerField(default=0)
    weigth = models.IntegerField(default=0)

    class Meta:
        abstract = True


class TrackableModel(EmptyModel):
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    created_by = models.CharField("row created by", max_length=200, default='NA')
    updated_at = models.DateTimeField(auto_now=True,null=True)
    updated_by = models.CharField("row updated by", max_length=200, default='NA')

    class Meta:
        abstract = True


class TrackableModelWithSeqAndStatus(TrackableModel):
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    seq = models.IntegerField(default=0)
    weigth = models.IntegerField(default=0)

    class Meta:
        abstract = True

# ------------------
# base model types
# ------------------


class BaseAuditHistory(EmptyModel):
    value_field = models.CharField(max_length=200, default='')
    new_value = models.CharField(max_length=200, default='')
    old_value = models.CharField(max_length=200, default='')
    updated_at = models.DateField(auto_now_add=True)
    updated_by_user_id = models.IntegerField(default=0)
    updated_by_user_name = models.CharField(max_length=200, default='')
    assigned_to_user_name = models.CharField(max_length=200, default='')
    ip = models.CharField(max_length=200, default='')
    meta_data = models.CharField(max_length=200, default='')
    group_name = models.CharField(max_length=200, default='')
    
    class Meta:
        abstract = True


class BaseQuestionSet(TrackableModelWithSeqAndStatus):
    is_mandatory = models.BooleanField(default=False)
    question_type = models.CharField(max_length=200, default='')
    question_key = models.CharField(max_length=200, default='')
    question_title = models.CharField(max_length=200, default='')
    question_sub_title = models.CharField(max_length=200, default='')
    question_help_text = models.CharField(max_length=200, default='')
    question_options = models.CharField(max_length=200, default='')
    question_validations = models.CharField(max_length=200, default='')
    
    class Meta:
        abstract = True
