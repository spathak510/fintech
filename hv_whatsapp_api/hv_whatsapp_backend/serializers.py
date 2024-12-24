from rest_framework import serializers
from hv_whatsapp_api.models import SSLChekDetails



class SSLCheckSerializer(serializers.ModelSerializer):

    class Meta:
        model = SSLChekDetails
        fields = '__all__'