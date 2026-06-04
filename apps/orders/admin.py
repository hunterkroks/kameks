from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity', 'get_cost')

    def get_cost(self, obj):
        return obj.get_cost()
    get_cost.short_description = 'Стоимость'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'phone', 'status', 'delivery_method', 'total', 'created_at')
    list_filter = ('status', 'buyer_type', 'delivery_method', 'payment_method')
    search_fields = ('order_number', 'full_name', 'phone', 'email', 'company_name', 'inn')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'order_number', 'items_total', 'total')
    inlines = [OrderItemInline]
