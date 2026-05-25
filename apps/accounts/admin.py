from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'company_name', 'inn')
    search_fields = ('user__username', 'user__email', 'company_name', 'inn')
