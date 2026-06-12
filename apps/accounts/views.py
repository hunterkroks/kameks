from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegisterForm, FlexLoginForm
from .models import UserProfile, DeliveryAddress, CompanyProfile, Notification, RecentlyViewed
from apps.orders.models import Order

MANAGER = {
    'name': 'Максим Корчагин',
    'phone': '+7 (917) 555-12-34',
    'initials': 'МК',
}

# Активные статусы для фильтра «в работе»
ACTIVE_STATUSES = Order.ACTIVE_STATUSES

# Цвет/класс бейджа по статусу
STATUS_CLASS = {
    'pending': 'status-pending',
    'confirmed': 'status-confirmed',
    'paid': 'status-paid',
    'shipped': 'status-shipped',
    'delivered': 'status-delivered',
    'cancelled': 'status-cancelled',
}

# Подстатус (короткая подпись под суммой)
STATUS_SUBLABEL = {
    'pending': 'Ожидает подтверждения',
    'confirmed': 'Ожидает оплаты',
    'paid': 'Оплачен',
    'shipped': 'В пути',
    'delivered': 'Получен',
    'cancelled': 'Отменён',
}

# Этапы прогресс-полосы и индекс активного этапа по статусу
PROGRESS_LABELS = ['Подтверждение', 'Оплата', 'Сборка', 'Доставка']
STATUS_PROGRESS_INDEX = {
    'pending': 0,
    'confirmed': 1,
    'paid': 2,
    'shipped': 3,
    'delivered': 4,  # все пройдены
}


# ──────────────────────────────────────────────────────────
# Регистрация / вход / выход
# ──────────────────────────────────────────────────────────
def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        # Серверная проверка согласия (JS можно обойти через DevTools)
        if not request.POST.get('agree'):
            form.add_error(None, 'Необходимо принять условия пользовательского соглашения')
            return render(request, 'accounts/register.html', {'form': form})
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать.')
            return redirect('accounts:profile')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = FlexLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            next_url = request.GET.get('next') or 'accounts:profile'
            return redirect(next_url)
    else:
        form = FlexLoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('main:index')


# ──────────────────────────────────────────────────────────
# Хелперы личного кабинета
# ──────────────────────────────────────────────────────────
def _get_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _sidebar_context(request, active):
    """Общий контекст сайдбара ЛК: карточка пользователя, счётчики, менеджер."""
    user = request.user
    profile = _get_profile(user)

    orders = Order.objects.filter(user=user)
    orders_count = orders.count()
    total_spent = orders.aggregate(s=Sum('total'))['s'] or 0

    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    addresses_count = DeliveryAddress.objects.filter(user=user).count()

    is_ul = profile.buyer_type == 'ul'
    company = getattr(user, 'company', None)
    if is_ul and company and company.company_name:
        display_name = company.company_name
    else:
        display_name = user.get_full_name() or user.username

    initials = ''.join([p[0] for p in (display_name or 'U').split()[:2]]).upper() or 'U'

    return {
        'active_section': active,
        'profile': profile,
        'is_ul': is_ul,
        'display_name': display_name,
        'user_initials': initials,
        'sb_orders_count': orders_count,
        'sb_total_spent': total_spent,
        'sb_unread_count': unread_count,
        'sb_addresses_count': addresses_count,
        'manager': MANAGER,
    }


def _prepare_order_cards(orders):
    """Готовит данные карточек заказов (всё посчитано во view)."""
    cards = []
    for order in orders:
        items = list(order.items.all())
        thumbs = []
        for it in items[:3]:
            img = it.product.get_main_image()
            thumbs.append({
                'url': img.image.url if img else '',
                'name': it.product.name,
            })
        extra_count = max(0, len(items) - 3)

        # Описание
        names = [it.product.name for it in items]
        if not names:
            description = 'Заказ без позиций'
        elif len(names) == 1:
            description = names[0]
        elif len(names) == 2:
            description = f'{names[0]}, {names[1]}'
        else:
            description = f'{names[0]}, {names[1]} и ещё {len(names) - 2} позиций'

        total_qty = sum(it.quantity for it in items)
        idx = STATUS_PROGRESS_INDEX.get(order.status, 0)
        progress = []
        is_active = order.status in ACTIVE_STATUSES
        if is_active:
            for i, label in enumerate(PROGRESS_LABELS):
                if i < idx:
                    state = 'done'
                elif i == idx:
                    state = 'active'
                else:
                    state = ''
                progress.append({'label': label, 'state': state})

        cards.append({
            'order': order,
            'thumbs': thumbs,
            'extra_count': extra_count,
            'description': description,
            'total_qty': total_qty,
            'positions_count': len(items),
            'status_class': STATUS_CLASS.get(order.status, ''),
            'status_label': order.get_status_display(),
            'status_sublabel': STATUS_SUBLABEL.get(order.status, ''),
            'delivery_label': order.get_delivery_method_display(),
            'payment_label': order.get_payment_method_display(),
            'is_active': is_active,
            'progress': progress,
        })
    return cards


def _filter_orders(orders, flt):
    if flt == 'active':
        return orders.filter(status__in=ACTIVE_STATUSES)
    if flt == 'completed':
        return orders.filter(status='delivered')
    if flt == 'cancelled':
        return orders.filter(status='cancelled')
    return orders


# ──────────────────────────────────────────────────────────
# Обзор
# ──────────────────────────────────────────────────────────
@login_required
def profile_overview(request):
    user = request.user
    ctx = _sidebar_context(request, 'overview')

    all_orders = Order.objects.filter(user=user).prefetch_related('items__product')
    orders_count = ctx['sb_orders_count']
    total_spent = ctx['sb_total_spent']
    active_count = all_orders.filter(status__in=ACTIVE_STATUSES).count()

    last_order = all_orders.first()
    days_since_last = None
    if last_order:
        days_since_last = (timezone.now().date() - last_order.created_at.date()).days

    # Прирост за месяц (для трендов)
    month_ago = timezone.now() - timedelta(days=30)
    orders_month = all_orders.filter(created_at__gte=month_ago).count()
    spent_month = all_orders.filter(created_at__gte=month_ago).aggregate(s=Sum('total'))['s'] or 0

    # Скидка (заглушка уровней)
    discount_percent = 5
    to_gold = 100000 - (total_spent or 0)
    if to_gold < 0:
        to_gold = 0

    recent_orders = all_orders[:4]
    order_cards = _prepare_order_cards(recent_orders)

    notifications = Notification.objects.filter(user=user)[:4]
    unread_count = ctx['sb_unread_count']

    # Недавно просмотренные
    recently = (RecentlyViewed.objects.filter(user=user)
                .select_related('product')
                .prefetch_related('product__images')[:4])
    recent_products = []
    for rv in recently:
        img = rv.product.get_main_image()
        recent_products.append({
            'product': rv.product,
            'img_url': img.image.url if img else '',
        })

    ctx.update({
        'orders_count': orders_count,
        'total_spent': total_spent,
        'active_count': active_count,
        'last_order': last_order,
        'days_since_last': days_since_last,
        'orders_month': orders_month,
        'spent_month': spent_month,
        'discount_percent': discount_percent,
        'to_gold': to_gold,
        'order_cards': order_cards,
        'notifications': notifications,
        'unread_count': unread_count,
        'recent_products': recent_products,
        'current_filter': 'all',
    })
    return render(request, 'accounts/profile_overview.html', ctx)


# ──────────────────────────────────────────────────────────
# Мои заказы
# ──────────────────────────────────────────────────────────
@login_required
def profile_orders(request):
    user = request.user
    ctx = _sidebar_context(request, 'orders')

    flt = request.GET.get('filter', 'all')
    search = (request.GET.get('q') or '').strip()

    orders = Order.objects.filter(user=user).prefetch_related('items__product')
    orders = _filter_orders(orders, flt)
    if search:
        from django.db.models import Q
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(items__product__name__icontains=search)
        ).distinct()

    paginator = Paginator(orders, 10)
    page = paginator.get_page(request.GET.get('page'))
    order_cards = _prepare_order_cards(page.object_list)

    all_orders = Order.objects.filter(user=user)
    ctx.update({
        'page_obj': page,
        'order_cards': order_cards,
        'current_filter': flt,
        'search_q': search,
        'count_all': all_orders.count(),
        'count_active': all_orders.filter(status__in=ACTIVE_STATUSES).count(),
        'count_completed': all_orders.filter(status='delivered').count(),
        'count_cancelled': all_orders.filter(status='cancelled').count(),
    })
    return render(request, 'accounts/profile_orders.html', ctx)


@login_required
def profile_order_detail(request, order_number):
    user = request.user
    ctx = _sidebar_context(request, 'orders')
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product__images'),
        order_number=order_number, user=user,
    )

    items = []
    for it in order.items.all():
        img = it.product.get_main_image()
        items.append({
            'item': it,
            'img_url': img.image.url if img else '',
            'cost': it.get_cost(),
        })

    idx = STATUS_PROGRESS_INDEX.get(order.status, 0)
    progress = []
    is_active = order.status in ACTIVE_STATUSES
    if is_active or order.status == 'delivered':
        for i, label in enumerate(PROGRESS_LABELS):
            state = 'done' if i < idx else ('active' if i == idx else '')
            progress.append({'label': label, 'state': state})

    ctx.update({
        'order': order,
        'order_items': items,
        'status_class': STATUS_CLASS.get(order.status, ''),
        'status_label': order.get_status_display(),
        'delivery_label': order.get_delivery_method_display(),
        'payment_label': order.get_payment_method_display(),
        'progress': progress,
        'is_active': is_active,
    })
    return render(request, 'accounts/profile_order_detail.html', ctx)


# ──────────────────────────────────────────────────────────
# Уведомления
# ──────────────────────────────────────────────────────────
@login_required
def profile_notifications(request):
    user = request.user
    ctx = _sidebar_context(request, 'notifications')

    type_filter = request.GET.get('type', 'all')
    notifications = Notification.objects.filter(user=user)
    if type_filter in ('order', 'delivery', 'promo', 'system'):
        notifications = notifications.filter(type=type_filter)

    paginator = Paginator(notifications, 20)
    page = paginator.get_page(request.GET.get('page'))

    ctx.update({
        'page_obj': page,
        'notifications': page.object_list,
        'type_filter': type_filter,
    })
    return render(request, 'accounts/profile_notifications.html', ctx)


@login_required
@require_POST
def notification_mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'success': True, 'unread': unread})


@login_required
@require_POST
def notification_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'unread': 0})
    return redirect('accounts:profile_notifications')


# ──────────────────────────────────────────────────────────
# Адреса
# ──────────────────────────────────────────────────────────
@login_required
def profile_addresses(request):
    ctx = _sidebar_context(request, 'addresses')
    ctx['addresses'] = DeliveryAddress.objects.filter(user=request.user)
    return render(request, 'accounts/profile_addresses.html', ctx)


def _save_address(request, address):
    address.title = (request.POST.get('title') or '').strip()
    address.city = (request.POST.get('city') or '').strip()
    address.address = (request.POST.get('address') or '').strip()
    is_default = bool(request.POST.get('is_default'))
    address.is_default = is_default
    address.user = request.user
    address.save()
    if is_default:
        DeliveryAddress.objects.filter(user=request.user).exclude(pk=address.pk).update(is_default=False)


@login_required
@require_POST
def address_add(request):
    _save_address(request, DeliveryAddress())
    messages.success(request, 'Адрес добавлен.')
    return redirect('accounts:profile_addresses')


@login_required
@require_POST
def address_edit(request, pk):
    address = get_object_or_404(DeliveryAddress, pk=pk, user=request.user)
    _save_address(request, address)
    messages.success(request, 'Адрес обновлён.')
    return redirect('accounts:profile_addresses')


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(DeliveryAddress, pk=pk, user=request.user)
    address.delete()
    messages.success(request, 'Адрес удалён.')
    return redirect('accounts:profile_addresses')


@login_required
@require_POST
def address_set_default(request, pk):
    address = get_object_or_404(DeliveryAddress, pk=pk, user=request.user)
    DeliveryAddress.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save(update_fields=['is_default'])
    messages.success(request, 'Адрес назначен основным.')
    return redirect('accounts:profile_addresses')


# ──────────────────────────────────────────────────────────
# Реквизиты (только ЮЛ)
# ──────────────────────────────────────────────────────────
@login_required
def profile_company(request):
    profile = _get_profile(request.user)
    if profile.buyer_type != 'ul':
        messages.info(request, 'Реквизиты доступны только для юридических лиц.')
        return redirect('accounts:profile_settings')

    company, _ = CompanyProfile.objects.get_or_create(
        user=request.user,
        defaults={'company_name': profile.company_name or '', 'inn': profile.inn or ''},
    )

    if request.method == 'POST':
        for field in ['company_name', 'inn', 'kpp', 'ogrn', 'legal_address',
                      'bank_name', 'bik', 'bank_account', 'correspondent_account']:
            setattr(company, field, (request.POST.get(field) or '').strip())
        company.save()
        messages.success(request, 'Реквизиты сохранены.')
        return redirect('accounts:profile_company')

    ctx = _sidebar_context(request, 'company')
    ctx['company'] = company
    return render(request, 'accounts/profile_company.html', ctx)


# ──────────────────────────────────────────────────────────
# Настройки
# ──────────────────────────────────────────────────────────
@login_required
def profile_settings(request):
    user = request.user
    profile = _get_profile(user)
    password_form = PasswordChangeForm(user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'personal':
            full_name = (request.POST.get('full_name') or '').strip()
            parts = full_name.split()
            user.last_name = parts[0] if parts else ''
            user.first_name = ' '.join(parts[1:]) if len(parts) > 1 else (parts[0] if parts else '')
            user.email = (request.POST.get('email') or '').strip()
            user.save()
            profile.phone = (request.POST.get('phone') or '').strip()
            profile.buyer_type = request.POST.get('buyer_type', 'fl')
            profile.save()
            messages.success(request, 'Личные данные обновлены.')
            return redirect('accounts:profile_settings')

        if action == 'password':
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль изменён.')
                return redirect('accounts:profile_settings')
            else:
                messages.error(request, 'Не удалось изменить пароль. Проверьте поля.')

        if action == 'notifications':
            profile.notify_order_email = bool(request.POST.get('notify_order_email'))
            profile.notify_promo_email = bool(request.POST.get('notify_promo_email'))
            profile.notify_delivery_sms = bool(request.POST.get('notify_delivery_sms'))
            profile.save()
            messages.success(request, 'Настройки уведомлений сохранены.')
            return redirect('accounts:profile_settings')

    ctx = _sidebar_context(request, 'settings')
    ctx['password_form'] = password_form
    ctx['full_name_value'] = user.get_full_name()
    return render(request, 'accounts/profile_settings.html', ctx)


# ──────────────────────────────────────────────────────────
# Повторить заказ
# ──────────────────────────────────────────────────────────
@login_required
def reorder(request, order_number):
    from apps.cart.cart import Cart
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    cart = Cart(request)
    added = 0
    for it in order.items.all():
        if it.product.is_active:
            cart.add(it.product, quantity=it.quantity)
            added += 1
    if added:
        messages.success(request, f'Товары из заказа {order.order_number} добавлены в корзину.')
    else:
        messages.warning(request, 'Товары из заказа больше недоступны.')
    return redirect('cart:detail')
