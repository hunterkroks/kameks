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
    list_display = ('id', 'first_name', 'last_name', 'phone', 'status', 'delivery_type', 'total_price', 'created_at')
    list_filter = ('status', 'delivery_type', 'payment_type')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    inlines = [OrderItemInline]
