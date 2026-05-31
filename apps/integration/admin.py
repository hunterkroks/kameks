from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html

from apps.integration.models import Exchange1CLog, ProductBackup
from apps.integration import views as integration_views


class ProductBackupInline(admin.TabularInline):
    model = ProductBackup
    extra = 0
    readonly_fields = ('product_id', 'sku', 'name', 'price', 'stock', 'is_active', 'action')
    can_delete = False
    max_num = 0
    verbose_name = 'Снимок товара'
    verbose_name_plural = 'Снимки товаров (бэкап)'


@admin.register(Exchange1CLog)
class Exchange1CLogAdmin(admin.ModelAdmin):
    list_display = (
        'filename', 'status_badge', 'created_at',
        'count_processed', 'count_created', 'count_price_updated',
        'count_stock_updated', 'count_no_sku', 'count_errors',
    )
    list_filter = ('status', 'created_at')
    readonly_fields = (
        'filename', 'status', 'created_at',
        'count_processed', 'count_created', 'count_price_updated',
        'count_stock_updated', 'count_no_sku', 'count_errors',
        'error_text', 'details',
    )
    inlines = [ProductBackupInline]

    def status_badge(self, obj):
        colors = {
            Exchange1CLog.STATUS_SUCCESS: ('green', '✅ Успех'),
            Exchange1CLog.STATUS_ERROR: ('red', '❌ Ошибка'),
            Exchange1CLog.STATUS_ROLLED_BACK: ('#e6a817', '↩️ Откатан'),
        }
        color, label = colors.get(obj.status, ('#999', obj.status))
        return format_html('<span style="color:{};font-weight:bold">{}</span>', color, label)
    status_badge.short_description = 'Статус'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'import-xml/',
                self.admin_site.admin_view(integration_views.import_view),
                name='integration_import',
            ),
            path(
                'import-xml/confirm/',
                self.admin_site.admin_view(integration_views.import_confirm_view),
                name='integration_import_confirm',
            ),
            path(
                'import-xml/result/<int:pk>/',
                self.admin_site.admin_view(integration_views.import_result_view),
                name='integration_import_result',
            ),
            path(
                'import-xml/rollback-last/',
                self.admin_site.admin_view(integration_views.rollback_last_view),
                name='integration_rollback_last',
            ),
            path(
                'export-catalog/',
                self.admin_site.admin_view(integration_views.export_catalog_view),
                name='integration_export_catalog',
            ),
        ]
        return custom + urls

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
