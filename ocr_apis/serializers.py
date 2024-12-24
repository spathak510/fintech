from attr import fields
from rest_framework import serializers
import urllib.request
from rest_framework.validators import ValidationError

from .models import (DrivingLicenseOcrFront, DrivingLicenseOcrBack, VoterIDOcrFront, VoterIDOcrBack, PassportIDOcrFront, PassportIDOcrBack, AadhaarOcrFront, AadhaarOcrBack, PanOcr)

class DrivingLicenseFrontSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DrivingLicenseOcrFront
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}

class DrivingLicenseBackSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DrivingLicenseOcrBack
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}

class VoterIDFrontSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = VoterIDOcrFront
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}

class VoterIDBackSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = VoterIDOcrBack
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}

class PassportIDFrontSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PassportIDOcrFront
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}

class PassportIDBackSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PassportIDOcrBack
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}

class AadhaarFrontOcrSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AadhaarOcrFront
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}

class AadhaarBackOcrSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AadhaarOcrBack
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}

class PanOcrSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PanOcr
        fields = '__all__'
        extra_kwargs = {'ocr_string': {'write_only': True}}