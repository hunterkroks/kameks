import logging
import os
import re
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import JsonResponse, Http404, FileResponse
from django.views.decorators.http import require_POST

from apps.cart.cart import Cart
from apps.catalog.models import Product
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


MANAGER_INFO = {
    'name': 'Максим Корчагин',
    'role': 'Ваш персональный менеджер',
    'phone': '+7 (917) 555-12-34',
    'email': 'manager@kameks.ru',
    'initials': 'МК',
}

DELIVERY_COSTS = {
    Order.DELIVERY_PICKUP: Decimal('0'),
    Order.DELIVERY_CDEK: Decimal('450'),
    Order.DELIVERY_DL: Decimal('680'),
    Order.DELIVERY_COURIER: Decimal('350'),
}

FREE_DELIVERY_THRESHOLD = Decimal('50000')


def _cart_items(cart):
    """Список позиций корзины с предзагруженными связями."""
    return list(cart)


def _calc_delivery_cost(method, items_total):
    base = DELIVERY_COSTS.get(method, Decimal('0'))
    if method != Order.DELIVERY_PICKUP and items_total >= FREE_DELIVERY_THRESHOLD:
        return Decimal('0')
    return base


def _build_invoice(order):
    """Генерирует текстовый счёт (reportlab не установлен) и сохраняет путь."""
    invoices_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
    os.makedirs(invoices_dir, exist_ok=True)
    filename = f'invoice_{order.order_number}.txt'
    path = os.path.join(invoices_dir, filename)

    lines = [
        'СЧЁТ НА ОПЛАТУ',
        f'№ {order.order_number} от {order.created_at:%d.%m.%Y}',
        '=' * 60,
        '',
        'Поставщик: ООО «КАМЭКС», ИНН 1650000000, КПП 165001001',
        'Адрес: г. Набережные Челны, пр. Машиностроительный, 1',
        '',
        'Покупатель:',
        f'  {order.company_name}',
        f'  ИНН {order.inn}  КПП {order.kpp}',
        f'  Контакт: {order.full_name}, {order.phone}, {order.email}',
        '',
        '-' * 60,
        f'{"№":<4}{"Наименование":<34}{"Кол":>5}{"Цена":>8}{"Сумма":>9}',
        '-' * 60,
    ]
    for i, item in enumerate(order.items.all(), 1):
        name = (item.product.name or item.product.sku)[:32]
        cost = item.get_cost()
        lines.append(f'{i:<4}{name:<34}{item.quantity:>5}{item.price:>8.0f}{cost:>9.0f}')
    lines += [
        '-' * 60,
        f'{"Товары:":>51}{order.items_total:>9.0f}',
    ]
    if order.discount:
        lines.append(f'{"Скидка:":>51}{("-" + str(int(order.discount))):>9}')
    lines += [
        f'{"Доставка:":>51}{order.delivery_cost:>9.0f}',
        f'{"ИТОГО К ОПЛАТЕ:":>51}{order.total:>9.0f}',
        '',
        'НДС не облагается.',
        'Счёт действителен 5 банковских дней.',
    ]
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    order.invoice_file = f'invoices/{filename}'
    order.save(update_fields=['invoice_file'])
    return path


def _send_notifications(order):
    items = list(order.items.all())
    rows = '\n'.join(
        f'  • {it.product.name or it.product.sku} × {it.quantity} = {it.get_cost():.0f} ₽'
        for it in items
    )
    delivery_label = order.get_delivery_method_display()
    payment_label = order.get_payment_method_display()

    body_common = (
        f'Заказ {order.order_number}\n'
        f'Покупатель: {order.full_name} ({order.get_buyer_type_display()})\n'
        f'Телефон: {order.phone}\nEmail: {order.email}\n'
    )
    if order.buyer_type == 'ul':
        body_common += f'Компания: {order.company_name}, ИНН {order.inn}, КПП {order.kpp}\n'
    body_common += (
        f'Доставка: {delivery_label}'
        + (f' — {order.delivery_city}, {order.delivery_address}\n' if order.delivery_method != Order.DELIVERY_PICKUP else '\n')
        + f'Оплата: {payment_label}\n'
        f'\nСостав заказа:\n{rows}\n\n'
        f'Товары: {order.items_total:.0f} ₽\n'
        + (f'Скидка: -{order.discount:.0f} ₽\n' if order.discount else '')
        + f'Доставка: {order.delivery_cost:.0f} ₽\n'
        f'ИТОГО: {order.total:.0f} ₽\n'
    )
    if order.comment:
        body_common += f'\nКомментарий: {order.comment}\n'

    # Клиенту
    send_mail(
        subject=f'КАМЭКС — заказ {order.order_number} принят',
        message=(
            f'Здравствуйте, {order.full_name}!\n\n'
            f'Спасибо за заказ. Мы свяжемся с вами в течение 30 минут для подтверждения.\n\n'
            + body_common +
            f'\nВаш менеджер: {MANAGER_INFO["name"]}, {MANAGER_INFO["phone"]}\n'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=True,
    )
    # Менеджеру
    send_mail(
        subject=f'Новый заказ {order.order_number}',
        message='НОВЫЙ ЗАКАЗ\n\n' + body_common,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[MANAGER_INFO['email']],
        fail_silently=True,
    )
    # Счёт для ЮЛ (отдельным письмом)
    if order.payment_method == Order.PAYMENT_INVOICE:
        send_mail(
            subject=f'Счёт на оплату по заказу {order.order_number}',
            message=(
                f'Здравствуйте!\n\nВо вложении (см. личный кабинет) счёт на оплату '
                f'по заказу {order.order_number} на сумму {order.total:.0f} ₽.\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=True,
        )


def _profile_initial(user):
    initial = {
        'full_name': (f'{user.last_name} {user.first_name}').strip(),
        'email': user.email or '',
    }
    profile = getattr(user, 'profile', None)
    if profile:
        initial['phone'] = profile.phone
        initial['company_name'] = profile.company_name
        initial['inn'] = profile.inn
        initial['delivery_address'] = profile.address
    return initial


def order_create(request):
    # --- Защита от дублирования: повторная отправка формы с тем же токеном
    # (двойной клик, F5, зависший запрос) ведёт на уже созданный заказ, а не плодит дубль.
    # Проверяем ДО проверки корзины: после успешного заказа корзина уже пуста.
    if request.method == 'POST':
        token = (request.POST.get('form_token') or '').strip()
        if token:
            existing = Order.objects.filter(idempotency_key=token).first()
            if existing is not None:
                return redirect('orders:success', order_number=existing.order_number)

    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart:detail')

    cart_items = _cart_items(cart)
    items_total = sum((it['total_price'] for it in cart_items), Decimal('0'))
    items_count = sum(it['quantity'] for it in cart_items)
    unique_items_count = len(cart_items)

    applied_promo = request.session.get('promo_code', '')
    discount = Decimal(str(request.session.get('promo_discount', '0') or '0'))

    if request.method == 'POST':
        data = request.POST
        errors = {}
        form_token = (data.get('form_token') or '').strip()

        buyer_type = data.get('buyer_type', 'fl')
        full_name = (data.get('full_name') or '').strip()
        phone = (data.get('phone') or '').strip()
        email = (data.get('email') or '').strip()
        company_name = (data.get('company_name') or '').strip()
        inn = (data.get('inn') or '').strip()
        kpp = (data.get('kpp') or '').strip()
        delivery_method = data.get('delivery_method', Order.DELIVERY_PICKUP)
        delivery_city = (data.get('delivery_city') or '').strip()
        delivery_address = (data.get('delivery_address') or '').strip()
        payment_method = data.get('payment_method', Order.PAYMENT_CARD)
        comment = (data.get('comment') or '').strip()
        agree = data.get('agree')

        if not full_name:
            errors['full_name'] = 'Укажите ФИО / контактное лицо'
        if not phone:
            errors['phone'] = 'Укажите телефон'
        if not email:
            errors['email'] = 'Укажите email'
        if buyer_type == 'ul':
            if not company_name:
                errors['company_name'] = 'Укажите название компании'
            if not re.fullmatch(r'\d{10}|\d{12}', inn):
                errors['inn'] = 'ИНН должен содержать 10 или 12 цифр'
        if delivery_method not in DELIVERY_COSTS:
            delivery_method = Order.DELIVERY_PICKUP
        if delivery_method != Order.DELIVERY_PICKUP and not delivery_city:
            errors['delivery_city'] = 'Укажите город доставки'
        if payment_method not in dict(Order.PAYMENT_CHOICES):
            payment_method = Order.PAYMENT_CARD
        if not agree:
            errors['agree'] = 'Необходимо согласие с условиями'

        delivery_cost = _calc_delivery_cost(delivery_method, items_total)
        total = items_total - discount + delivery_cost

        if errors:
            context = _checkout_context(
                cart_items, items_total, discount, delivery_cost, total,
                applied_promo, items_count, unique_items_count,
            )
            context.update({
                'errors': errors,
                'form_data': data,
                'form_token': form_token or uuid.uuid4().hex,
            })
            return render(request, 'orders/checkout.html', context)

        if not request.session.session_key:
            request.session.save()

        # Ключ идемпотентности: токен из формы либо разовый (если форма без токена).
        idem_key = form_token or uuid.uuid4().hex

        try:
            with transaction.atomic():
                order = Order(
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key or '',
                    idempotency_key=idem_key,
                    buyer_type=buyer_type,
                    full_name=full_name,
                    phone=phone,
                    email=email,
                    company_name=company_name,
                    inn=inn,
                    kpp=kpp,
                    delivery_method=delivery_method,
                    delivery_city=delivery_city,
                    delivery_address=delivery_address,
                    delivery_cost=delivery_cost,
                    payment_method=payment_method,
                    items_total=items_total,
                    discount=discount,
                    promo_code=applied_promo,
                    total=total,
                    comment=comment,
                    subscribe_news=bool(data.get('subscribe_news')),
                    status=Order.STATUS_PENDING,
                )
                order.save()

                order_items = [
                    OrderItem(
                        order=order,
                        product=item['product'],
                        price=item['price'],
                        quantity=item['quantity'],
                    )
                    for item in cart_items
                ]
                OrderItem.objects.bulk_create(order_items)
        except IntegrityError:
            # Параллельный запрос с тем же токеном успел создать заказ первым —
            # просто ведём пользователя на уже созданный заказ, без дубля.
            existing = Order.objects.filter(idempotency_key=idem_key).first()
            if existing is not None:
                cart.clear()
                request.session.pop('promo_code', None)
                request.session.pop('promo_discount', None)
                return redirect('orders:success', order_number=existing.order_number)
            raise

        if payment_method == Order.PAYMENT_INVOICE:
            try:
                _build_invoice(order)
            except Exception:
                logger.exception('Не удалось сформировать счёт для заказа %s', order.order_number)

        # Отправка уведомлений не должна блокировать оформление заказа:
        # при недоступном SMTP письмо просто не уйдёт, но заказ уже сохранён в БД.
        try:
            _send_notifications(order)
        except Exception:
            logger.exception('Не удалось отправить уведомления по заказу %s', order.order_number)

        cart.clear()
        request.session.pop('promo_code', None)
        request.session.pop('promo_discount', None)

        return redirect('orders:success', order_number=order.order_number)

    # GET
    delivery_cost = Decimal('0')
    total = items_total - discount + delivery_cost
    context = _checkout_context(
        cart_items, items_total, discount, delivery_cost, total,
        applied_promo, items_count, unique_items_count,
    )
    initial = {}
    if request.user.is_authenticated:
        initial = _profile_initial(request.user)
    context['form_data'] = initial
    context['errors'] = {}
    context['form_token'] = uuid.uuid4().hex
    return render(request, 'orders/checkout.html', context)


def _checkout_context(cart_items, items_total, discount, delivery_cost, total,
                      applied_promo, items_count, unique_items_count):
    return {
        'cart_items': cart_items,
        'items_total': items_total,
        'discount': discount,
        'delivery_cost': delivery_cost,
        'total': total,
        'applied_promo': applied_promo,
        'items_count': items_count,
        'unique_items_count': unique_items_count,
        'manager_info': MANAGER_INFO,
        'free_delivery_threshold': FREE_DELIVERY_THRESHOLD,
        'has_free_delivery': items_total >= FREE_DELIVERY_THRESHOLD,
        'cdek_cost': DELIVERY_COSTS[Order.DELIVERY_CDEK],
        'dl_cost': DELIVERY_COSTS[Order.DELIVERY_DL],
        'courier_cost': DELIVERY_COSTS[Order.DELIVERY_COURIER],
    }


@require_POST
def quick_order(request):
    """Быстрый заказ «Купить в 1 клик» — имя, телефон, товар. AJAX."""
    name = (request.POST.get('name') or '').strip()
    phone = (request.POST.get('phone') or '').strip()
    product_id = request.POST.get('product_id')

    if not name or not phone or not product_id:
        return JsonResponse(
            {'success': False, 'error': 'Заполните имя и телефон'}, status=400
        )

    product = get_object_or_404(Product, id=product_id, is_active=True)

    order = Order(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key or '',
        full_name=name,
        phone=phone,
        email=request.user.email if request.user.is_authenticated and request.user.email else 'no-email@kameks.local',
        status=Order.STATUS_PENDING,
        comment='Быстрый заказ («Купить в 1 клик»)',
        items_total=product.current_price,
        total=product.current_price,
    )
    order.save()
    OrderItem.objects.create(
        order=order,
        product=product,
        price=product.current_price,
        quantity=1,
    )

    return JsonResponse({'success': True, 'order_id': order.pk, 'order_number': order.order_number})


def order_success(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        order_number=order_number,
    )
    # Доступ: владелец, либо анонимный заказ из той же сессии
    if order.user_id:
        if not request.user.is_authenticated or order.user_id != request.user.id:
            raise PermissionDenied
    else:
        if order.session_key and order.session_key != request.session.session_key:
            raise PermissionDenied

    order_items = list(order.items.all())
    context = {
        'order': order,
        'order_items': order_items,
        'is_invoice': order.payment_method == Order.PAYMENT_INVOICE,
        'delivery_label': order.get_delivery_method_display(),
        'payment_label': order.get_payment_method_display(),
        'manager_info': MANAGER_INFO,
        'has_invoice_file': bool(order.invoice_file),
    }
    return render(request, 'orders/order_success.html', context)


def order_invoice(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if order.user_id:
        if not request.user.is_authenticated or order.user_id != request.user.id:
            raise PermissionDenied
    elif order.session_key and order.session_key != request.session.session_key:
        raise PermissionDenied
    if not order.invoice_file:
        raise Http404
    path = os.path.join(settings.MEDIA_ROOT, order.invoice_file)
    if not os.path.exists(path):
        raise Http404
    return FileResponse(open(path, 'rb'), as_attachment=True,
                        filename=os.path.basename(path))


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    if order.user != request.user:
        raise PermissionDenied
    return render(request, 'orders/order_detail.html', {'order': order})
