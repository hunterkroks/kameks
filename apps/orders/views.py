from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.cart.cart import Cart
from apps.catalog.models import Product
from .models import Order, OrderItem
from .forms import OrderCreateForm


@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart:detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.total_price = cart.get_total_price()
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
            cart.clear()
            return redirect('orders:success', pk=order.pk)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
            }
        form = OrderCreateForm(initial=initial)

    return render(request, 'orders/checkout.html', {'cart': cart, 'form': form})


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

    # Имя может быть из нескольких слов — первое в first_name, остальное в last_name
    parts = name.split(None, 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else '—'

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=request.user.email if request.user.is_authenticated and request.user.email else 'no-email@kameks.local',
        status=Order.STATUS_NEW,
        comment='Быстрый заказ («Купить в 1 клик»)',
        total_price=product.current_price,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        price=product.current_price,
        quantity=1,
    )

    return JsonResponse({'success': True, 'order_id': order.pk})


def order_success(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=pk)
    if order.user != request.user:
        raise PermissionDenied
    return render(request, 'orders/order_detail.html', {'order': order})
