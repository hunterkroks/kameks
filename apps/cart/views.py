from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.catalog.models import Product
from .cart import Cart


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'redirect': '/accounts/login/'}, status=401)
        return redirect(f'/accounts/login/?next=/cart/add/{product_id}/')
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    override = bool(request.POST.get('override', False))

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
