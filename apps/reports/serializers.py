from rest_framework import serializers
from .models import Query


class QuerySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%d.%m.%Y %H:%M")
    
    class Meta:
        model = Query
        fields = ['id', 'created_at', 'vin', 'marka', 'tip', 'cost'] 