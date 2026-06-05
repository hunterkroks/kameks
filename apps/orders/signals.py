import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from apps.orders.models import Order

logger = logging.getLogger(__name__)


# Статусы при которых списываем остаток
DEDUCT_ON_STATUSES = {Order.STATUS_SHIPPED, Order.STATUS_DELIVERED}

# Статусы при которых возвращаем остаток обратно
RESTORE_ON_STATUSES = {Order.STATUS_CANCELLED}


@receiver(pre_save, sender=Order)
def handle_stock_on_status_change(sender, instance, **kwargs):
    if not instance.pk:
        instance._status_changed_from = None
        return  # новый заказ — ещё не сохранён

    try:
        old = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        instance._status_changed_from = None
        return

    old_status = old.status
    new_status = instance.status
    # Сохраняем для post_save: с какого статуса перешли (None если не менялся)
    instance._status_changed_from = old_status if old_status != new_status else None
    if old_status == new_status:
        return  # статус не изменился

    # Списываем остаток при переходе в "Отправлен" или "Доставлен"
    if new_status in DEDUCT_ON_STATUSES and not instance.stock_deducted:
        with transaction.atomic():
            for item in instance.items.select_related('product'):
                product = item.product
                product.stock = max(0, product.stock - item.quantity)
                product.save(update_fields=['stock', 'updated_at'])
        instance.stock_deducted = True

    # Возвращаем остаток при отмене — но только если уже списали
    elif new_status in RESTORE_ON_STATUSES and instance.stock_deducted:
        with transaction.atomic():
            for item in instance.items.select_related('product'):
                product = item.product
                product.stock += item.quantity
                product.save(update_fields=['stock', 'updated_at'])
        instance.stock_deducted = False


# ── Уведомления при смене статуса заказа ──────────────────────────
# Текст уведомления по новому статусу. {num} — номер заказа.
STATUS_NOTIFICATIONS = {
    Order.STATUS_CONFIRMED: ('order', 'Заказ {num} подтверждён',
                             'Ваш заказ {num} подтверждён менеджером и принят в работу.'),
    Order.STATUS_PAID: ('order', 'Получена оплата по заказу {num}',
                        'Мы получили оплату по заказу {num}. Заказ передан на сборку.'),
    Order.STATUS_SHIPPED: ('delivery', 'Заказ {num} передан в доставку',
                           'Заказ {num} передан в доставку.{track}'),
    Order.STATUS_DELIVERED: ('delivery', 'Заказ {num} доставлен',
                             'Заказ {num} доставлен. Будем рады, если вы оставите отзыв.'),
    Order.STATUS_CANCELLED: ('order', 'Заказ {num} отменён',
                             'Заказ {num} был отменён. Если это ошибка — свяжитесь с менеджером.'),
}


@receiver(post_save, sender=Order)
def notify_on_status_change(sender, instance, created, **kwargs):
    if created:
        return
    changed_from = getattr(instance, '_status_changed_from', None)
    if not changed_from:
        return
    new_status = instance.status
    tpl = STATUS_NOTIFICATIONS.get(new_status)
    if not tpl:
        return
    ntype, title_tpl, text_tpl = tpl
    num = instance.order_number or f'#{instance.pk}'
    track = ''
    if new_status == Order.STATUS_SHIPPED and instance.tracking_number:
        track = f' Трек-номер для отслеживания: {instance.tracking_number}.'
    title = title_tpl.format(num=num)
    text = text_tpl.format(num=num, track=track)

    # Уведомление в БД (только для зарегистрированных пользователей)
    if instance.user_id:
        try:
            from apps.accounts.models import Notification
            Notification.objects.create(
                user_id=instance.user_id,
                type=ntype,
                title=title,
                text=text,
                link=f'/accounts/profile/orders/{instance.order_number}/',
            )
        except Exception:
            logger.exception('Не удалось создать Notification по заказу %s', num)

    # Дублируем письмом (в dev — console backend)
    if instance.email:
        try:
            send_mail(
                subject=f'КАМЭКС — {title}',
                message=f'Здравствуйте, {instance.full_name}!\n\n{text}\n\nС уважением, КАМЭКС.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=True,
            )
        except Exception:
            logger.exception('Не удалось отправить письмо о смене статуса заказа %s', num)
