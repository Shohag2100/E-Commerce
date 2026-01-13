from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'product_price', 'quantity', 'subtotal']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'email', 'status', 'total_amount', 'paid', 'created_at']
    list_filter = ['status', 'paid', 'created_at']
    search_fields = ['order_number', 'email', 'first_name', 'last_name']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'total_amount', 'stripe_payment_intent', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'total_amount', 'notes')
        }),
        ('Customer Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'postal_code', 'country')
        }),
        ('Payment Information', {
            'fields': ('stripe_payment_intent', 'paid', 'paid_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )