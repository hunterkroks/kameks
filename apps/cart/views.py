from decimal import Decimal
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from apps.catalog.models import Product
from .cart import Cart
from .models import SavedItem, PromoCode

# ── Константы доставки ────────────────────────────────────
FREE_DELIVERY_THRESHOLD = 50000
DELIVERY_OPTIONS = {
    'pickup': {'label': 'Самовывоз', 'cost': 0},
    'cdek': {'label': 'СДЭК', 'cost': 450},
    'dellin': {'label': 'Деловые Линии', 'cost': 680},
}


def _delivery_cost(method, items_total):
    """Стоимость доставки с учётом порога бесплатной доставки."""
    if method == 'pickup':
        return 0
    if items_total >= FREE_DELIVERY_THRESHOLD:
        return 0
    return DELIVERY_OPTIONS.get(method, DELIVERY_OPTIONS['pickup'])['cost']


def _promo_discount(code, items_total):
    """Возвращает (PromoCode|None, discount_decimal). Валидирует код."""
    if not code:
        return None, Decimal('0')
    promo = PromoCode.objects.filter(code__iexact=code, is_active=True).first()
    if not promo:
        return None, Decimal('0')
    if promo.valid_until and promo.valid_until < date.today():
        return None, Decimal('0')
    if items_total < promo.min_order_amount:
        return None, Decimal('0')
    discount = (items_total * Decimal(promo.discount_percent) / Decimal('100'))
    return promo, discount


def _saved_items_for(request):
    if request.user.is_authenticated:
        return SavedItem.objects.filter(user=request.user).select_related('product').prefetch_related('product__images')
    if not request.session.session_key:
        request.session.save()
    return SavedItem.objects.filter(session_key=request.session.session_key).select_related('product').prefetch_related('product__images')


def cart_detail(request):
    cart = Cart(request)

    # Собираем позиции с готовыми вычислениями (ничего не считаем в шаблоне)
    cart_items = []
    items_total = Decimal('0')
    items_count = 0
    total_weight = Decimal('0')
    cart_category_ids = set()
    cart_product_ids = []

    for item in cart:
        product = item['product']
        line_total = item['total_price']
        items_total += line_total
        items_count += item['quantity']
        if product.weight:
            total_weight += product.weight * item['quantity']
        cart_category_ids.add(product.category_id)
        cart_product_ids.append(product.id)

        manufacturer = product.attributes.filter(name='Производитель').first()
        if product.stock <= 0:
            stock_label, stock_color = 'Под заказ', '#C86A00'
        elif product.stock <= 3:
            stock_label, stock_color = f'Осталось {product.stock} шт.', '#C86A00'
        else:
            stock_label, stock_color = 'В наличии', '#1A7035'

        cart_items.append({
            'product': product,
            'quantity': item['quantity'],
            'price': item['price'],
            'total': line_total,
            'manufacturer': manufacturer,
            'brands': list(product.brands.all()[:3]),
            'stock_label': stock_label,
            'stock_color': stock_color,
        })

    # Промокод
    applied_promo_code = request.session.get('promo_code')
    promo, discount = _promo_discount(applied_promo_code, items_total)
    if applied_promo_code and not promo:
        # код стал невалидным (сумма упала ниже минимума и т.п.) — убираем
        request.session.pop('promo_code', None)
        applied_promo_code = None

    # Доставка
    selected_delivery = request.session.get('delivery_method', 'pickup')
    if selected_delivery not in DELIVERY_OPTIONS:
        selected_delivery = 'pickup'
    delivery_cost = _delivery_cost(selected_delivery, items_total)

    total = items_total - discount + delivery_cost

    # Рекомендации: товары из тех же категорий, исключая корзину
    recommended_products = []
    if cart_category_ids:
        recommended_products = list(
            Product.objects.filter(category_id__in=cart_category_ids, is_active=True)
            .exclude(id__in=cart_product_ids)
            .prefetch_related('images')[:4]
        )

    free_remaining = max(Decimal('0'), Decimal(FREE_DELIVERY_THRESHOLD) - items_total)
    free_progress = min(100, float(items_total / FREE_DELIVERY_THRESHOLD * 100)) if items_total else 0

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'items_total': items_total,
        'items_count': items_count,
        'unique_items_count': len(cart_items),
        'discount': discount,
        'delivery_cost': delivery_cost,
        'total': total,
        'free_delivery_threshold': FREE_DELIVERY_THRESHOLD,
        'free_delivery_remaining': free_remaining,
        'free_delivery_progress': free_progress,
        'free_delivery_reached': items_total >= FREE_DELIVERY_THRESHOLD,
        'total_weight': total_weight,
        'recommended_products': recommended_products,
        'saved_items': _saved_items_for(request),
        'applied_promo': promo,
        'applied_promo_code': applied_promo_code,
        'discount_percent': promo.discount_percent if promo else 0,
        'selected_delivery': selected_delivery,
        'delivery_options': DELIVERY_OPTIONS,
    }
    return render(request, 'cart/cart.html', context)


@require_POST
def cart_add(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'redirect': '/accounts/login/'}, status=401)
        return redirect(f'/accounts/login/?next=/cart/add/{product_id}/')
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    # ВАЖНО: bool('false') == True в Python, поэтому парсим строку явно
    override_raw = str(request.POST.get('override', '')).lower()
    override = override_raw in ('true', '1', 'yes', 'on')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Сколько этого товара уже в корзине
    current_quantity = cart.cart.get(str(product_id), {}).get('quantity', 0)

    # Итоговое количество с учётом уже лежащего в корзине
    if override:
        new_quantity = quantity
    else:
        new_quantity = current_quantity + quantity

    if new_quantity < 0:
        new_quantity = 0

    # Проверка стока с учётом того, что уже в корзине
    if new_quantity > product.stock:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'error': 'stock_exceeded',
                'message': f'Доступно только {product.stock} шт. '
                           f'У вас в корзине уже {current_quantity} шт.',
                'available': max(0, product.stock - current_quantity),
                'cart_quantity': current_quantity,
                'cart_total_items': len(cart),
                'product_id': product.id,
            }, status=400)
        return redirect('cart:detail')

    cart.add(product=product, quantity=new_quantity, override_quantity=True)

    if is_ajax:
        from decimal import Decimal
        price = Decimal(cart.cart.get(str(product_id), {}).get('price', product.current_price))
        return JsonResponse({
            'success': True,
            'cart_quantity': new_quantity,
            'cart_total_items': len(cart),
            'available_to_add': max(0, product.stock - new_quantity),
            'product_id': product.id,
            'stock': product.stock,
            'item_total': float(price * new_quantity),
            'cart_grand_total': float(cart.get_total_price()),
            # обратная совместимость со старым JS
            'cart_total': len(cart),
            'item_quantity': new_quantity,
        })
    return redirect('cart:detail')


@require_POST
def cart_remove(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'redirect': '/accounts/login/'}, status=401)
        return redirect('/accounts/login/')
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total': len(cart),
            'item_quantity': 0,
            'cart_grand_total': float(cart.get_total_price()),
        })
    return redirect('cart:detail')


# ════════════════════════════════════════════════════════════
#  ОТЛОЖЕННЫЕ ТОВАРЫ (Save for Later)
# ════════════════════════════════════════════════════════════

@require_POST
def move_to_saved(request, product_id):
    """Убрать товар из корзины и отложить."""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)

    if request.user.is_authenticated:
        SavedItem.objects.get_or_create(user=request.user, product=product)
    else:
        if not request.session.session_key:
            request.session.save()
        SavedItem.objects.get_or_create(
            session_key=request.session.session_key, product=product
        )

    return JsonResponse({
        'success': True,
        'cart_total': len(cart),
        'cart_grand_total': float(cart.get_total_price()),
    })


@require_POST
def restore_from_saved(request, saved_id):
    """Вернуть отложенный товар в корзину."""
    saved = get_object_or_404(SavedItem, id=saved_id)
    # Проверка владельца
    if request.user.is_authenticated:
        if saved.user_id != request.user.id:
            return JsonResponse({'success': False}, status=403)
    else:
        if saved.session_key != request.session.session_key:
            return JsonResponse({'success': False}, status=403)

    cart = Cart(request)
    product = saved.product
    qty = 1
    if product.stock > 0:
        qty = min(1, product.stock)
    cart.add(product=product, quantity=max(1, qty))
    saved.delete()

    return JsonResponse({
        'success': True,
        'cart_total': len(cart),
        'cart_grand_total': float(cart.get_total_price()),
        'product_id': product.id,
    })


# ════════════════════════════════════════════════════════════
#  ПРОМОКОДЫ
# ════════════════════════════════════════════════════════════

@require_POST
def apply_promo(request):
    code = (request.POST.get('code') or '').strip()
    if not code:
        return JsonResponse({'success': False, 'error': 'Введите промокод'}, status=400)

    cart = Cart(request)
    items_total = cart.get_total_price()

    promo = PromoCode.objects.filter(code__iexact=code, is_active=True).first()
    if not promo:
        return JsonResponse({'success': False, 'error': 'Промокод не найден или неактивен'}, status=400)
    if promo.valid_until and promo.valid_until < date.today():
        return JsonResponse({'success': False, 'error': 'Срок действия промокода истёк'}, status=400)
    if items_total < promo.min_order_amount:
        return JsonResponse({
            'success': False,
            'error': f'Промокод действует от {promo.min_order_amount} ₽',
        }, status=400)

    request.session['promo_code'] = promo.code

    discount = items_total * Decimal(promo.discount_percent) / Decimal('100')
    selected_delivery = request.session.get('delivery_method', 'pickup')
    delivery_cost = _delivery_cost(selected_delivery, items_total)
    total = items_total - discount + delivery_cost

    return JsonResponse({
        'success': True,
        'code': promo.code,
        'discount_percent': promo.discount_percent,
        'discount': float(discount),
        'delivery_cost': float(delivery_cost),
        'total': float(total),
        'items_total': float(items_total),
    })


@require_POST
def remove_promo(request):
    request.session.pop('promo_code', None)
    cart = Cart(request)
    items_total = cart.get_total_price()
    selected_delivery = request.session.get('delivery_method', 'pickup')
    delivery_cost = _delivery_cost(selected_delivery, items_total)
    return JsonResponse({
        'success': True,
        'delivery_cost': float(delivery_cost),
        'total': float(items_total + delivery_cost),
        'items_total': float(items_total),
    })


# ════════════════════════════════════════════════════════════
#  ДОСТАВКА
# ════════════════════════════════════════════════════════════

@require_POST
def set_delivery(request):
    method = request.POST.get('method', 'pickup')
    if method not in DELIVERY_OPTIONS:
        return JsonResponse({'success': False, 'error': 'Неизвестный способ доставки'}, status=400)
    request.session['delivery_method'] = method

    cart = Cart(request)
    items_total = cart.get_total_price()
    delivery_cost = _delivery_cost(method, items_total)

    promo, discount = _promo_discount(request.session.get('promo_code'), items_total)
    total = items_total - discount + delivery_cost

    return JsonResponse({
        'success': True,
        'method': method,
        'delivery_cost': float(delivery_cost),
        'free': delivery_cost == 0 and method != 'pickup',
        'discount': float(discount),
        'total': float(total),
        'items_total': float(items_total),
    })


# ════════════════════════════════════════════════════════════
#  СПЕЦИФИКАЦИЯ: PDF + EMAIL
# ════════════════════════════════════════════════════════════

def _build_spec_rows(cart):
    rows = []
    for item in cart:
        product = item['product']
        mfr = product.attributes.filter(name='Производитель').first()
        rows.append({
            'sku': product.sku,
            'name': product.name,
            'manufacturer': mfr.value if mfr else '—',
            'quantity': item['quantity'],
            'price': item['price'],
            'total': item['total_price'],
        })
    return rows


def download_spec(request):
    """PDF-спецификация (коммерческое предложение) по корзине."""
    cart = Cart(request)
    rows = _build_spec_rows(cart)
    if not rows:
        return redirect('cart:detail')

    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Кириллический шрифт
    font_name = 'Helvetica'
    try:
        import os
        font_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('AppFont', font_path))
            font_name = 'AppFont'
        else:
            dejavu = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            if os.path.exists(dejavu):
                pdfmetrics.registerFont(TTFont('AppFont', dejavu))
                font_name = 'AppFont'
    except Exception:
        font_name = 'Helvetica'

    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    now = timezone.localtime()
    kp_number = now.strftime('%y%m%d-%H%M')

    y = h - 25 * mm
    p.setFont(font_name, 16)
    p.drawString(20 * mm, y, 'ООО «ПКФ КАМЭКС»')
    y -= 7 * mm
    p.setFont(font_name, 9)
    p.setFillColor(colors.grey)
    p.drawString(20 * mm, y, 'г. Набережные Челны, Промышленная ул. 50, оф. 106  ·  +7 (800) 123-45-67')
    y -= 5 * mm
    p.drawString(20 * mm, y, 'info@kameks.ru')
    p.setFillColor(colors.black)

    y -= 12 * mm
    p.setFont(font_name, 13)
    p.drawString(20 * mm, y, f'Коммерческое предложение № {kp_number}')
    y -= 6 * mm
    p.setFont(font_name, 9)
    p.setFillColor(colors.grey)
    p.drawString(20 * mm, y, f'от {now.strftime("%d.%m.%Y %H:%M")}')
    p.setFillColor(colors.black)

    # Заголовок таблицы
    y -= 12 * mm
    p.setFont(font_name, 8)
    p.setFillColor(colors.HexColor('#1B3A5C'))
    p.rect(20 * mm, y - 2 * mm, w - 40 * mm, 7 * mm, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.drawString(22 * mm, y, 'Артикул')
    p.drawString(48 * mm, y, 'Наименование')
    p.drawString(120 * mm, y, 'Произв.')
    p.drawString(150 * mm, y, 'Кол-во')
    p.drawString(168 * mm, y, 'Цена')
    p.drawString(185 * mm, y, 'Сумма')
    p.setFillColor(colors.black)

    y -= 9 * mm
    p.setFont(font_name, 8)
    grand = Decimal('0')
    for r in rows:
        if y < 30 * mm:
            p.showPage()
            y = h - 25 * mm
            p.setFont(font_name, 8)
        p.drawString(22 * mm, y, str(r['sku'])[:14])
        p.drawString(48 * mm, y, str(r['name'])[:42])
        p.drawString(120 * mm, y, str(r['manufacturer'])[:12])
        p.drawString(152 * mm, y, str(r['quantity']))
        p.drawString(166 * mm, y, f"{r['price']:.0f}")
        p.drawString(183 * mm, y, f"{r['total']:.0f}")
        grand += r['total']
        y -= 6 * mm

    y -= 4 * mm
    p.setLineWidth(0.5)
    p.line(20 * mm, y, w - 20 * mm, y)
    y -= 8 * mm
    p.setFont(font_name, 11)
    p.drawRightString(w - 20 * mm, y, f'ИТОГО: {grand:.0f} ₽')

    y -= 14 * mm
    p.setFont(font_name, 7)
    p.setFillColor(colors.grey)
    p.drawString(20 * mm, y, 'Цены указаны без учёта доставки. Предложение действительно 3 дня. Не является публичной офертой.')

    p.showPage()
    p.save()
    buf.seek(0)

    resp = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="kameks-kp-{kp_number}.pdf"'
    return resp


@require_POST
def email_spec(request):
    """Отправить спецификацию на email (console backend в dev)."""
    email = (request.POST.get('email') or '').strip()
    if not email:
        return JsonResponse({'success': False, 'error': 'Укажите email'}, status=400)

    cart = Cart(request)
    rows = _build_spec_rows(cart)
    if not rows:
        return JsonResponse({'success': False, 'error': 'Корзина пуста'}, status=400)

    lines = ['Спецификация заказа КАМЭКС', '']
    grand = Decimal('0')
    for r in rows:
        lines.append(f"{r['sku']} — {r['name']} ({r['manufacturer']}) | "
                     f"{r['quantity']} шт × {r['price']:.0f} ₽ = {r['total']:.0f} ₽")
        grand += r['total']
    lines += ['', f'ИТОГО: {grand:.0f} ₽']
    body = '\n'.join(lines)

    try:
        send_mail(
            subject='Спецификация заказа — КАМЭКС',
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@kameks.ru'),
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception:
        return JsonResponse({'success': False, 'error': 'Не удалось отправить письмо'}, status=500)

    return JsonResponse({'success': True})


# ════════════════════════════════════════════════════════════
#  B2B: ЗАПРОС СЧЁТА
# ════════════════════════════════════════════════════════════

@require_POST
def request_invoice(request):
    company = (request.POST.get('company') or '').strip()
    inn = (request.POST.get('inn') or '').strip()
    email = (request.POST.get('email') or '').strip()
    phone = (request.POST.get('phone') or '').strip()
    comment = (request.POST.get('comment') or '').strip()

    if not company or not inn or not (email or phone):
        return JsonResponse(
            {'success': False, 'error': 'Заполните название компании, ИНН и контакт'},
            status=400,
        )

    cart = Cart(request)
    rows = _build_spec_rows(cart)
    spec = '\n'.join(
        f"{r['sku']} — {r['name']} × {r['quantity']} = {r['total']:.0f} ₽" for r in rows
    )

    body = (
        f'Запрос счёта (B2B)\n\n'
        f'Компания: {company}\nИНН: {inn}\nEmail: {email}\nТелефон: {phone}\n'
        f'Комментарий: {comment}\n\nСостав заказа:\n{spec}\n'
    )

    # Сохраняем заявку — отправляем письмо менеджеру (console в dev)
    try:
        send_mail(
            subject=f'Запрос счёта B2B — {company}',
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@kameks.ru'),
            recipient_list=[getattr(settings, 'MANAGER_EMAIL', 'info@kameks.ru')],
            fail_silently=True,
        )
    except Exception:
        pass

    return JsonResponse({'success': True})
