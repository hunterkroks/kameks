from django.contrib import admin
from .models import SavedItem, PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'min_order_amount', 'is_active', 'valid_until')
    list_filter = ('is_active',)
    search_fields = ('code',)


@admin.register(SavedItem)
class SavedItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'session_key', 'created_at')
    list_filter = ('created_at',)
