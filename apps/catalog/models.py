from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Brand(models.Model):
    """Марка автомобиля (КАМАЗ, МАЗ, Урал и т.д.)"""
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    logo = models.ImageField('Логотип', upload_to='brands/', blank=True)
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Марка автомобиля'
        verbose_name_plural = 'Марки автомобилей'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:by_brand', kwargs={'slug': self.slug})


class CarModel(models.Model):
    """Модель автомобиля (КАМАЗ-65115, МАЗ-5440)"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='models', verbose_name='Марка')
    name = models.CharField('Название', max_length=150)
    slug = models.SlugField('Slug')
    year_from = models.PositiveSmallIntegerField('Год выпуска (с)', null=True, blank=True)
    year_to = models.PositiveSmallIntegerField('Год выпуска (по)', null=True, blank=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Модель автомобиля'
        verbose_name_plural = 'Модели автомобилей'
        ordering = ['brand', 'name']
        unique_together = ('brand', 'slug')

    def __str__(self):
        return f'{self.brand.name} {self.name}'


class Category(models.Model):
    """Категория запчастей с поддержкой иерархии (Двигатель → Поршневая группа)"""
    name = models.CharField('Название', max_length=150)
    slug = models.SlugField('Slug', unique=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children', verbose_name='Родительская категория'
    )
    image = models.ImageField('Изображение', upload_to='categories/', blank=True)
    icon = models.CharField('CSS-класс иконки', max_length=50, blank=True, help_text='bi-gear, bi-tools и т.д.')
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} → {self.name}'
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:catalog') + f'?category={self.slug}'


class Product(models.Model):
    """Товар — запчасть"""
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='Категория')
    brands = models.ManyToManyField(Brand, blank=True, verbose_name='Применимые марки', related_name='products')
    car_models = models.ManyToManyField(CarModel, blank=True, verbose_name='Применимые модели', related_name='products')

    name = models.CharField('Название', max_length=300)
    slug = models.SlugField('Slug', unique=True, max_length=350)
    sku = models.CharField('Артикул (собственный)', max_length=100, unique=True)
    oem_number = models.CharField('OEM-номер', max_length=100, blank=True, db_index=True)
    description = models.TextField('Описание', blank=True)
    specifications = models.TextField('Характеристики (JSON)', blank=True,
                                      help_text='Ключ: значение, по одному на строку')

    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    discount_price = models.DecimalField('Цена со скидкой', max_digits=10, decimal_places=2, null=True, blank=True)

    stock = models.PositiveIntegerField('Остаток на складе', default=0)
    weight = models.DecimalField('Вес (кг)', max_digits=7, decimal_places=3, null=True, blank=True)

    is_original = models.BooleanField('Оригинальная запчасть', default=True)
    is_active = models.BooleanField('Активен', default=True)
    is_bestseller = models.BooleanField('Хит продаж', default=False)
    is_new = models.BooleanField('Новинка', default=False)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sku} — {self.name}'

    def get_absolute_url(self):
        return reverse('catalog:product', kwargs={'slug': self.slug})

    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percent(self):
        if self.discount_price and self.price:
            return int((1 - self.discount_price / self.price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    def get_main_image(self):
        img = self.images.filter(is_main=True).first()
        return img or self.images.first()


class ProductImage(models.Model):
    """Фотографии товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Товар')
    image = models.ImageField('Фото', upload_to='products/')
    is_main = models.BooleanField('Главное фото', default=False)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Фото товара'
        verbose_name_plural = 'Фото товаров'
        ordering = ['-is_main', 'order']

    def __str__(self):
        return f'Фото #{self.pk} → {self.product.sku}'


class Analogue(models.Model):
    """Аналоги и кросс-номера"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='analogues', verbose_name='Товар')
    brand_name = models.CharField('Бренд-аналог', max_length=100)
    part_number = models.CharField('Артикул аналога', max_length=100, db_index=True)

    class Meta:
        verbose_name = 'Аналог'
        verbose_name_plural = 'Аналоги'

    def __str__(self):
        return f'{self.brand_name} {self.part_number}'
