from django.shortcuts import render
from django.contrib import messages
from django.db.models import Sum
from .models import Banner, Review, Partner, Advantage
from apps.catalog.models import Category, Product, Brand
from apps.orders.models import OrderItem


def about(request):
    return render(request, 'main/about.html')


def delivery(request):
    return render(request, 'main/delivery.html')


def contacts(request):
    if request.method == 'POST':
        messages.success(request, 'Заявка принята! Менеджер свяжется с вами в течение 30 минут.')
    return render(request, 'main/contacts.html')


def _get_popular_products():
    """Возвращает 8 товаров: сначала по реальным заказам, иначе по флагу, иначе случайные."""
    ordered_ids = list(
        OrderItem.objects
        .values('product_id')
        .annotate(total=Sum('quantity'))
        .order_by('-total')
        .values_list('product_id', flat=True)[:8]
    )
    if ordered_ids:
        prods = {
            p.id: p for p in
            Product.objects.filter(id__in=ordered_ids, is_active=True)
            .select_related('category').prefetch_related('images')
        }
        return [prods[i] for i in ordered_ids if i in prods]

    bestsellers = list(
        Product.objects.filter(is_active=True, is_bestseller=True)
        .select_related('category').prefetch_related('images')[:8]
    )
    if bestsellers:
        return bestsellers

    return list(
        Product.objects.filter(is_active=True)
        .select_related('category').prefetch_related('images')
        .order_by('?')[:8]
    )


def index(request):
    advantages = Advantage.objects.all()
    categories = Category.objects.filter(parent__isnull=True, is_active=True)
    bestsellers = _get_popular_products()
    new_products = list(
        Product.objects.filter(is_active=True, is_new=True)
        .select_related('category').prefetch_related('images')[:8]
    )
    if not new_products:
        new_products = list(
            Product.objects.filter(is_active=True)
            .select_related('category').prefetch_related('images')
            .order_by('-id')[:8]
        )
    reviews = Review.objects.filter(is_active=True)[:6]
    brands = Brand.objects.filter(is_active=True).order_by('order', 'name')

    context = {
        'advantages': advantages,
        'categories': categories,
        'bestsellers': bestsellers,
        'new_products': new_products,
        'reviews': reviews,
        'brands': brands,
    }
    return render(request, 'main/index.html', context)
