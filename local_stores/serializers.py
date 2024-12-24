from rest_framework import serializers
from local_stores.models import LandingPageUser, NavigantUsersDetail
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate

# User Serializer
class LandinfPageUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingPageUser
        fields = '__all__'
            
            
            
class NavigantUsersDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = NavigantUsersDetail
        fields = '__all__'            