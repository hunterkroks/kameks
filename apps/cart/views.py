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
    override = request.POST.get('override', False)

    # Clamp quantity to available stock
    if quantity > product.stock:
        quantity = product.stock
    if quantity < 0:
        quantity = 0

    cart.add(product=product, quantity=quantity, override_quantity=bool(override))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item_quantity = cart.cart.get(str(product_id), {}).get('quantity', 0)
        from decimal import Decimal
        price = Decimal(cart.cart.get(str(product_id), {}).get('price', product.current_price))
        return JsonResponse({
            'cart_total': len(cart),
            'success': True,
            'item_quantity': item_quantity,
            'item_total': float(price * item_quantity),
            'cart_grand_total': float(cart.get_total_price()),
            'stock': product.stock,
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
