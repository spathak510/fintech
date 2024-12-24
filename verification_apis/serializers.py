from rest_framework import serializers

from .models import (DrivingLicenseVerification, PANVerification, PassportVerification,
                    VoterIDVerification, AadhaarVerification, CriminalVerification)

from hv_whatsapp_api.models import criminal_result_external

class DrivingLicenseVerificationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DrivingLicenseVerification
        exclude = ("source_api_response", )

class PANVerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PANVerification
        exclude = ("source_api_response", )

class PassportVerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PassportVerification
        exclude = ("source_api_response", )

class VoterIDVerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = VoterIDVerification
        exclude = ("source_api_response", )

class AadhaarVerificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = AadhaarVerification
        exclude = ("source_api_response", )

class CriminalCheckSerializer(serializers.ModelSerializer):

    class Meta:
        model = CriminalVerification
        fields = '__all__'
        
class GetCriminalExternalCheckSerializer(serializers.ModelSerializer):

    class Meta:
        model = criminal_result_external
        fields = '__all__'        
