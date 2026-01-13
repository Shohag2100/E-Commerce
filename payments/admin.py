from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['stripe_payment_intent_id', 'order__order_number', 'order__email']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_payment_method', 
                      'stripe_customer_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'amount', 'currency', 'status')
        }),
        ('Stripe Details', {
            'fields': ('stripe_payment_intent_id', 'stripe_payment_method', 'stripe_customer_id')
        }),
        ('Error Information', {
            'fields': ('error_message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )