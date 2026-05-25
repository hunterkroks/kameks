from django.contrib import admin
from .models import Brand, CarModel, Category, Product, ProductImage, Analogue


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


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class AnalogueInline(admin.TabularInline):
    model = Analogue
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'price', 'stock', 'is_active', 'is_bestseller', 'is_new')
    list_editable = ('price', 'stock', 'is_active', 'is_bestseller', 'is_new')
    list_filter = ('category', 'brands', 'is_active', 'is_bestseller', 'is_new', 'is_original')
    search_fields = ('sku', 'name', 'oem_number')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('brands', 'car_models')
    inlines = [ProductImageInline, AnalogueInline]
    readonly_fields = ('created_at', 'updated_at')
