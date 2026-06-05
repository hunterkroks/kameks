from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfile(models.Model):
    BUYER_TYPE_CHOICES = [
        ('fl', 'Физическое лицо'),
        ('ul', 'Юридическое лицо'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='Пользователь')
    buyer_type = models.CharField('Тип покупателя', max_length=2, choices=BUYER_TYPE_CHOICES, default='fl')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    company_name = models.CharField('Название компании', max_length=200, blank=True)
    inn = models.CharField('ИНН', max_length=12, blank=True)
    address = models.TextField('Адрес доставки', blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True)

    # Настройки уведомлений
    notify_order_email = models.BooleanField('Email о статусе заказа', default=True)
    notify_promo_email = models.BooleanField('Email об акциях', default=False)
    notify_delivery_sms = models.BooleanField('SMS о доставке', default=False)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль: {self.user.username}'


class DeliveryAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='Пользователь')
    title = models.CharField('Название', max_length=100)
    city = models.CharField('Город', max_length=100)
    address = models.CharField('Адрес', max_length=500)
    is_default = models.BooleanField('По умолчанию', default=False)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Адрес доставки'
        verbose_name_plural = 'Адреса доставки'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.title}: {self.city}, {self.address}'


class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company', verbose_name='Пользователь')
    company_name = models.CharField('Название компании', max_length=255)
    inn = models.CharField('ИНН', max_length=12)
    kpp = models.CharField('КПП', max_length=9, blank=True)
    ogrn = models.CharField('ОГРН', max_length=15, blank=True)
    legal_address = models.CharField('Юридический адрес', max_length=500, blank=True)
    bank_name = models.CharField('Банк', max_length=255, blank=True)
    bik = models.CharField('БИК', max_length=9, blank=True)
    bank_account = models.CharField('Расчётный счёт', max_length=20, blank=True)
    correspondent_account = models.CharField('Корр. счёт', max_length=20, blank=True)

    class Meta:
        verbose_name = 'Реквизиты компании'
        verbose_name_plural = 'Реквизиты компаний'

    def __str__(self):
        return self.company_name


class Notification(models.Model):
    TYPE_ORDER = 'order'
    TYPE_DELIVERY = 'delivery'
    TYPE_PROMO = 'promo'
    TYPE_SYSTEM = 'system'

    TYPES = [
        (TYPE_ORDER, 'Заказ'),
        (TYPE_DELIVERY, 'Доставка'),
        (TYPE_PROMO, 'Акция'),
        (TYPE_SYSTEM, 'Система'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='Пользователь')
    type = models.CharField('Тип', max_length=20, choices=TYPES, default=TYPE_SYSTEM)
    title = models.CharField('Заголовок', max_length=255)
    text = models.TextField('Текст')
    link = models.CharField('Ссылка', max_length=500, blank=True)
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_type_display()}: {self.title}'


class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed',
                             null=True, blank=True, verbose_name='Пользователь')
    session_key = models.CharField('Ключ сессии', max_length=40, null=True, blank=True)
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name='Товар')
    viewed_at = models.DateTimeField('Просмотрено', auto_now=True)

    class Meta:
        verbose_name = 'Просмотренный товар'
        verbose_name_plural = 'Просмотренные товары'
        ordering = ['-viewed_at']
        unique_together = [('user', 'product'), ('session_key', 'product')]

    def __str__(self):
        return f'{self.product} ({self.viewed_at:%d.%m.%Y})'
