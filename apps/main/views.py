from django.shortcuts import render
from django.contrib import messages
from .models import Banner, Review, Partner, Advantage
from apps.catalog.models import Category, Product, Brand


def about(request):
    return render(request, 'main/about.html')


def delivery(request):
    return render(request, 'main/delivery.html')


def contacts(request):
    if request.method == 'POST':
        messages.success(request, 'Заявка принята! Менеджер свяжется с вами в течение 30 минут.')
    return render(request, 'main/contacts.html')


def index(request):
    advantages = Advantage.objects.all()
    categories = Category.objects.filter(parent__isnull=True, is_active=True)
    bestsellers = Product.objects.filter(is_active=True, is_bestseller=True).select_related('category').prefetch_related('images')[:8]
    new_products = Product.objects.filter(is_active=True, is_new=True).select_related('category').prefetch_related('images')[:8]
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
