from rest_framework import serializers
from external_apis.models import GstVerification, McaVerification
import json

class GstVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GstVerification
        fields = ('gst_number', 'company_pan_number', 'gst_status','last_tax_paid_date','raw_response')
        extra_kwargs = {
            'raw_response': {'write_only': True}
        }


class McaVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = McaVerification
        fields = ('cin_number', 'company_name', 'status','address','industry','incorporation_date','directors','raw_response')
        extra_kwargs = {
            'raw_response': {'write_only': True}
        }

    def to_representation(self, instance):
        data = super(McaVerificationSerializer, self).to_representation(instance)
        data["directors"] = eval(data["directors"])
        return data

