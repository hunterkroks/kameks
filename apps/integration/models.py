from django.db import models


class Exchange1CLog(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_ERROR = 'error'
    STATUS_ROLLED_BACK = 'rolled_back'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успех'),
        (STATUS_ERROR, 'Ошибка'),
        (STATUS_ROLLED_BACK, 'Откатан'),
    ]

    filename = models.CharField('Имя файла', max_length=255)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField('Дата импорта', auto_now_add=True)

    count_processed = models.PositiveIntegerField('Обработано товаров', default=0)
    count_created = models.PositiveIntegerField('Создано новых', default=0)
    count_price_updated = models.PositiveIntegerField('Обновлено цен', default=0)
    count_stock_updated = models.PositiveIntegerField('Обновлено остатков', default=0)
    count_no_sku = models.PositiveIntegerField('Без артикула', default=0)
    count_errors = models.PositiveIntegerField('Ошибок', default=0)

    error_text = models.TextField('Текст ошибки', blank=True)
    details = models.TextField('Детали (JSON)', blank=True)

    class Meta:
        verbose_name = 'Лог обмена с 1С'
        verbose_name_plural = 'Логи обмена с 1С'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.filename} — {self.get_status_display()} ({self.created_at:%d.%m.%Y %H:%M})'


class ProductBackup(models.Model):
    """Снимок товара перед импортом — для возможности отката"""
    log = models.ForeignKey(Exchange1CLog, on_delete=models.CASCADE, related_name='backups', verbose_name='Лог импорта')
    product_id = models.PositiveIntegerField('ID товара')
    sku = models.CharField('Артикул', max_length=100)
    name = models.CharField('Название', max_length=300)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField('Остаток')
    is_active = models.BooleanField('Активен')
    action = models.CharField('Действие', max_length=20, choices=[
        ('created', 'Создан'),
        ('updated', 'Обновлён'),
    ])

    class Meta:
        verbose_name = 'Бэкап товара'
        verbose_name_plural = 'Бэкапы товаров'

    def __str__(self):
        return f'{self.sku} [{self.action}]'
