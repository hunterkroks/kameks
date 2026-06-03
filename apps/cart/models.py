from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SavedItem(models.Model):
    """Отложенный товар (Save for Later). Привязан к юзеру или к сессии гостя."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             related_name='saved_items', verbose_name='Пользователь')
    session_key = models.CharField('Ключ сессии', max_length=40, null=True, blank=True)
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE,
                                verbose_name='Товар')
    created_at = models.DateTimeField('Отложен', auto_now_add=True)

    class Meta:
        verbose_name = 'Отложенный товар'
        verbose_name_plural = 'Отложенные товары'
        ordering = ['-created_at']

    def __str__(self):
        owner = self.user or self.session_key
        return f'{owner} → {self.product.sku}'


class PromoCode(models.Model):
    """Промокод со скидкой в процентах."""
    code = models.CharField('Код', max_length=30, unique=True)
    discount_percent = models.IntegerField('Скидка, %', default=0)
    min_order_amount = models.IntegerField('Минимальная сумма заказа', default=0)
    is_active = models.BooleanField('Активен', default=True)
    valid_until = models.DateField('Действует до', null=True, blank=True)

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} (−{self.discount_percent}%)'
