from django.contrib import admin
from .models import (UserProfile, DeliveryAddress, CompanyProfile,
                     Notification, RecentlyViewed)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'buyer_type', 'phone', 'company_name', 'inn')
    list_filter = ('buyer_type',)
    search_fields = ('user__username', 'user__email', 'company_name', 'inn')


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'city', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('user__username', 'title', 'city', 'address')


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'inn', 'kpp')
    search_fields = ('company_name', 'inn', 'user__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read')
    search_fields = ('user__username', 'title', 'text')


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'product', 'viewed_at')
    search_fields = ('user__username', 'product__name', 'product__sku')
