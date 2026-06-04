from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
from apps.catalog.models import Product

User = get_user_model()


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Новый'),
        (STATUS_CONFIRMED, 'Подтверждён'),
        (STATUS_PAID, 'Оплачен'),
        (STATUS_SHIPPED, 'Отправлен'),
        (STATUS_DELIVERED, 'Доставлен'),
        (STATUS_CANCELLED, 'Отменён'),
    ]

    BUYER_TYPE_CHOICES = [
        ('fl', 'Физическое лицо'),
        ('ul', 'Юридическое лицо'),
    ]

    DELIVERY_PICKUP = 'pickup'
    DELIVERY_CDEK = 'cdek'
    DELIVERY_DL = 'dl'
    DELIVERY_COURIER = 'courier'

    DELIVERY_CHOICES = [
        (DELIVERY_PICKUP, 'Самовывоз'),
        (DELIVERY_CDEK, 'СДЭК'),
        (DELIVERY_DL, 'Деловые Линии'),
        (DELIVERY_COURIER, 'Курьер по городу'),
    ]

    PAYMENT_CARD = 'card'
    PAYMENT_SBP = 'sbp'
    PAYMENT_ON_DELIVERY = 'on_delivery'
    PAYMENT_INVOICE = 'invoice'

    PAYMENT_CHOICES = [
        (PAYMENT_CARD, 'Картой онлайн'),
        (PAYMENT_SBP, 'СБП'),
        (PAYMENT_ON_DELIVERY, 'При получении'),
        (PAYMENT_INVOICE, 'Безналичный расчёт (счёт)'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='orders', verbose_name='Пользователь')
    session_key = models.CharField('Ключ сессии', max_length=40, blank=True, db_index=True)

    buyer_type = models.CharField('Тип покупателя', max_length=2,
                                  choices=BUYER_TYPE_CHOICES, default='fl')

    # Контактные данные / поля ФЛ
    full_name = models.CharField('ФИО', max_length=200, default='')
    phone = models.CharField('Телефон', max_length=20, default='')
    email = models.EmailField('Email', default='')

    # Поля ЮЛ
    company_name = models.CharField('Название компании', max_length=255, blank=True)
    inn = models.CharField('ИНН', max_length=12, blank=True)
    kpp = models.CharField('КПП', max_length=9, blank=True)

    # Доставка
    delivery_method = models.CharField('Способ доставки', max_length=20,
                                       choices=DELIVERY_CHOICES, default=DELIVERY_PICKUP)
    delivery_city = models.CharField('Город', max_length=100, blank=True)
    delivery_address = models.CharField('Адрес доставки', max_length=500, blank=True)
    delivery_cost = models.DecimalField('Стоимость доставки', max_digits=10, decimal_places=2, default=0)

    # Оплата
    payment_method = models.CharField('Способ оплаты', max_length=20,
                                      choices=PAYMENT_CHOICES, default=PAYMENT_CARD)

    # Суммы
    items_total = models.DecimalField('Сумма товаров', max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField('Скидка', max_digits=10, decimal_places=2, default=0)
    promo_code = models.CharField('Промокод', max_length=30, blank=True)
    total = models.DecimalField('Итого', max_digits=12, decimal_places=2, default=0)

    comment = models.TextField('Комментарий к заказу', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)

    order_number = models.CharField('Номер заказа', max_length=20, unique=True, blank=True)
    invoice_file = models.CharField('Файл счёта', max_length=300, blank=True)

    subscribe_news = models.BooleanField('Подписка на акции', default=False)

    # Интеграция (сохранено из прежней модели)
    exported_to_1c = models.BooleanField('Выгружен в 1С', default=False)
    exported_at = models.DateTimeField('Дата выгрузки в 1С', null=True, blank=True)
    stock_deducted = models.BooleanField('Остаток списан', default=False)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ {self.order_number or self.pk} от {self.full_name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.order_number:
            self.order_number = f'К-{datetime.now().year}-{self.pk:05d}'
            super().save(update_fields=['order_number'])

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
