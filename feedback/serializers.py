from rest_framework import serializers
from feedback.models import VendorFeedback

# User Serializer
class VendorFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorFeedback
        fields = '__all__'