from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'subtotal']
        read_only_fields = ['product_name', 'product_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'email', 'first_name', 'last_name', 'phone', 
                  'address', 'city', 'postal_code', 'country', 'status', 'status_display',
                  'total_amount', 'notes', 'paid', 'paid_at', 'items', 'created_at', 'updated_at']
        read_only_fields = ['order_number', 'status', 'total_amount', 'paid', 'paid_at']

class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['email', 'first_name', 'last_name', 'phone', 'address', 
                  'city', 'postal_code', 'country', 'notes']
    
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required")
        return value