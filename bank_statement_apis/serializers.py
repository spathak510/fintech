from rest_framework.serializers import ModelSerializer
from . import models as Models

class LinkGenerateSerializer(ModelSerializer):

    class Meta:
        model = Models.LinkGenerateLogs
        fields = "__all__"
