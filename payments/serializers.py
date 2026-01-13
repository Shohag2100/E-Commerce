from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'order', 'order_number', 'stripe_payment_intent_id', 
                  'amount', 'currency', 'status', 'status_display', 
                  'error_message', 'created_at', 'updated_at']
        read_only_fields = ['stripe_payment_intent_id', 'status', 'error_message']
