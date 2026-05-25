from django.db import models


class Banner(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    subtitle = models.CharField('Подзаголовок', max_length=300, blank=True)
    image = models.ImageField('Изображение', upload_to='banners/')
    button_text = models.CharField('Текст кнопки', max_length=50, blank=True)
    button_url = models.CharField('Ссылка кнопки', max_length=200, blank=True)
    is_active = models.BooleanField('Активен', default=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
        ordering = ['order']

    def __str__(self):
        return self.title


class Review(models.Model):
    author_name = models.CharField('Имя автора', max_length=100)
    author_company = models.CharField('Компания', max_length=150, blank=True)
    text = models.TextField('Текст отзыва')
    rating = models.PositiveSmallIntegerField('Рейтинг', default=5, choices=[(i, i) for i in range(1, 6)])
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateField('Дата', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author_name} — {self.rating}★'


class Partner(models.Model):
    name = models.CharField('Название', max_length=100)
    logo = models.ImageField('Логотип', upload_to='partners/')
    website = models.URLField('Сайт', blank=True)
    order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Партнёр'
        verbose_name_plural = 'Партнёры'
        ordering = ['order']

    def __str__(self):
        return self.name


class Advantage(models.Model):
    icon = models.CharField('CSS-класс иконки', max_length=50, help_text='Например: bi-shield-check')
    title = models.CharField('Заголовок', max_length=100)
    description = models.TextField('Описание')
    order = models.PositiveSmallIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Преимущество'
        verbose_name_plural = 'Преимущества'
        ordering = ['order']

    def __str__(self):
        return self.title
