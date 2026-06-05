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
    actions = (
        'mark_confirmed', 'mark_paid', 'mark_shipped',
        'mark_delivered', 'mark_cancelled',
    )

    def _set_status(self, request, queryset, status, label):
        """Меняет статус по одному (через save() — чтобы сработали сигналы и уведомления)."""
        count = 0
        for order in queryset:
            if order.status != status:
                order.status = status
                order.save()
                count += 1
        self.message_user(request, f'Обновлено заказов: {count} → «{label}».')

    @admin.action(description='Подтвердить выбранные заказы')
    def mark_confirmed(self, request, queryset):
        self._set_status(request, queryset, Order.STATUS_CONFIRMED, 'Подтверждён')

    @admin.action(description='Отметить оплаченными')
    def mark_paid(self, request, queryset):
        self._set_status(request, queryset, Order.STATUS_PAID, 'Оплачен')

    @admin.action(description='Отправить (в путь)')
    def mark_shipped(self, request, queryset):
        self._set_status(request, queryset, Order.STATUS_SHIPPED, 'В пути')

    @admin.action(description='Отметить доставленными')
    def mark_delivered(self, request, queryset):
        self._set_status(request, queryset, Order.STATUS_DELIVERED, 'Доставлен')

    @admin.action(description='Отменить выбранные заказы')
    def mark_cancelled(self, request, queryset):
        self._set_status(request, queryset, Order.STATUS_CANCELLED, 'Отменён')
