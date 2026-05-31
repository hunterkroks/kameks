from django.db import transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.orders.models import Order


# Статусы при которых списываем остаток
DEDUCT_ON_STATUSES = {Order.STATUS_SHIPPED, Order.STATUS_DELIVERED}

# Статусы при которых возвращаем остаток обратно
RESTORE_ON_STATUSES = {Order.STATUS_CANCELLED}


@receiver(pre_save, sender=Order)
def handle_stock_on_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # новый заказ — ещё не сохранён

    try:
        old = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    old_status = old.status
    new_status = instance.status
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
