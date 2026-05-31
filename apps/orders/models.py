from django.db import models
from django.contrib.auth import get_user_model
from apps.catalog.models import Product

User = get_user_model()


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Новый'),
        (STATUS_CONFIRMED, 'Подтверждён'),
        (STATUS_SHIPPED, 'Отправлен'),
        (STATUS_DELIVERED, 'Доставлен'),
        (STATUS_CANCELLED, 'Отменён'),
    ]

    DELIVERY_PICKUP = 'pickup'
    DELIVERY_COURIER = 'courier'
    DELIVERY_TC = 'transport_company'

    DELIVERY_CHOICES = [
        (DELIVERY_PICKUP, 'Самовывоз'),
        (DELIVERY_COURIER, 'Курьер'),
        (DELIVERY_TC, 'Транспортная компания'),
    ]

    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_INVOICE = 'invoice'

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Наличные'),
        (PAYMENT_CARD, 'Банковская карта'),
        (PAYMENT_INVOICE, 'Счёт (для юр. лиц)'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='orders', verbose_name='Пользователь')
    # Контактные данные (дублируем на случай гостевого заказа)
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email')
    company = models.CharField('Компания', max_length=200, blank=True)

    delivery_type = models.CharField('Способ доставки', max_length=30, choices=DELIVERY_CHOICES, default=DELIVERY_PICKUP)
    delivery_address = models.TextField('Адрес доставки', blank=True)
    delivery_city = models.CharField('Город', max_length=100, blank=True)

    payment_type = models.CharField('Способ оплаты', max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_CARD)

    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    comment = models.TextField('Комментарий к заказу', blank=True)

    total_price = models.DecimalField('Итого', max_digits=12, decimal_places=2, default=0)
    exported_to_1c = models.BooleanField('Выгружен в 1С', default=False)
    exported_at = models.DateTimeField('Дата выгрузки в 1С', null=True, blank=True)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk} от {self.first_name} {self.last_name}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')
    price = models.DecimalField('Цена на момент заказа', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество', default=1)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product.sku} × {self.quantity}'

    def get_cost(self):
        return self.price * self.quantity
