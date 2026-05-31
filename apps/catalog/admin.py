from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Brand, CarModel, Category, Product, ProductImage, Analogue, ProductAttribute


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'brand', 'year_from', 'year_to', 'is_active')
    list_filter = ('brand', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter = ('parent', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


class DeleteButtonMixin:
    """Заменяет чекбокс 'Удалить?' на красную кнопку ✕"""
    class Media:
        css = {'all': ('css/inline_delete_btn.css',)}


class ProductImageInline(DeleteButtonMixin, admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:60px;">', obj.image.url)
        return '—'
    image_preview.short_description = 'Превью'


class AnalogueInline(DeleteButtonMixin, admin.TabularInline):
    model = Analogue
    extra = 1


class ProductAttributeInline(DeleteButtonMixin, admin.TabularInline):
    model = ProductAttribute
    extra = 1
    fields = ('name', 'value', 'order')


class NoSkuFilter(admin.SimpleListFilter):
    title = 'Без артикула'
    parameter_name = 'no_sku'

    def lookups(self, request, model_admin):
        return [('1', 'Только без артикула')]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(no_sku=True)
        return queryset


class LastImportFilter(admin.SimpleListFilter):
    title = 'Из последнего импорта'
    parameter_name = 'last_import'

    def lookups(self, request, model_admin):
        from apps.integration.models import Exchange1CLog
        log = Exchange1CLog.objects.filter(status='success').first()
        if log:
            return [('1', f'Новые из «{log.filename}»')]
        return []

    def queryset(self, request, queryset):
        if self.value() == '1':
            from apps.integration.models import Exchange1CLog
            log = Exchange1CLog.objects.filter(status='success').first()
            if log:
                ids = log.backups.filter(action='created').values_list('product_id', flat=True)
                return queryset.filter(pk__in=ids)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku_with_badge', 'thumbnail', 'name', 'category',
        'price', 'stock', 'is_active', 'updated_at',
    )
    list_filter = (
        'category', 'brands', 'is_active', 'is_bestseller',
        'is_new', 'is_original', NoSkuFilter, LastImportFilter,
    )
    search_fields = ('sku', 'name', 'oem_number')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('brands', 'car_models')
    inlines = [ProductImageInline, ProductAttributeInline, AnalogueInline]
    readonly_fields = ('created_at', 'updated_at')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['last_import_url'] = self._last_import_url()
        return super().changelist_view(request, extra_context=extra_context)

    def _last_import_url(self):
        """URL для фильтра по товарам из последнего импорта."""
        from apps.integration.models import Exchange1CLog
        log = Exchange1CLog.objects.filter(status='success').first()
        if log and log.backups.filter(action='created').exists():
            base = reverse('admin:catalog_product_changelist')
            return f'{base}?last_import=1'
        return None

    def thumbnail(self, obj):
        img = obj.get_main_image()
        if img and img.image:
            return format_html(
                '<img src="{}" style="height:48px;width:48px;object-fit:cover;border-radius:3px;">',
                img.image.url,
            )
        return format_html(
            '<span style="display:inline-block;height:48px;width:48px;background:#eee;'
            'border-radius:3px;text-align:center;line-height:48px;">{}</span>',
            '📷',
        )
    thumbnail.short_description = 'Фото'

    def sku_with_badge(self, obj):
        if obj.no_sku:
            return format_html(
                '{}&nbsp;<span style="background:#e6a817;color:#fff;font-size:11px;'
                'padding:2px 6px;border-radius:3px;font-weight:bold;">Без артикула</span>',
                obj.sku,
            )
        return obj.sku
    sku_with_badge.short_description = 'Артикул'
    sku_with_badge.admin_order_field = 'sku'
