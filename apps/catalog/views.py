from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, Product, Brand

SORT_MAP = {
    'popular': '-created_at',
    'price': 'price',
    '-price': '-price',
}


def catalog(request):
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')

    brand_slugs = request.GET.getlist('brand')
    category_slugs = request.GET.getlist('category')
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    in_stock = request.GET.get('in_stock')
    original = request.GET.get('original', '')
    search_q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'popular')

    if search_q:
        products = products.filter(
            Q(name__icontains=search_q) |
            Q(sku__icontains=search_q) |
            Q(oem_number__icontains=search_q)
        )

    current_brands = Brand.objects.none()
    current_categories = Category.objects.none()

    if brand_slugs:
        current_brands = Brand.objects.filter(slug__in=brand_slugs, is_active=True)
        products = products.filter(brands__slug__in=brand_slugs).distinct()

    if category_slugs:
        current_categories = Category.objects.filter(slug__in=category_slugs, is_active=True)
        # Собираем все категории: сам slug + все потомки (L2→L3, L1→L2+L3)
        all_cat_ids = set()
        for cat in current_categories:
            all_cat_ids.add(cat.pk)
            # дети
            children = list(cat.children.filter(is_active=True).values_list('pk', flat=True))
            all_cat_ids.update(children)
            # внуки
            grandchildren = Category.objects.filter(
                parent__pk__in=children, is_active=True
            ).values_list('pk', flat=True)
            all_cat_ids.update(grandchildren)
        products = products.filter(category__pk__in=all_cat_ids)

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

    if in_stock:
        products = products.filter(stock__gt=0)
    if original == '1':
        products = products.filter(is_original=True)
    elif original == '0':
        products = products.filter(is_original=False)

    order = SORT_MAP.get(sort, '-created_at')
    products = products.order_by(order)

    paginator = Paginator(products, 12)
    products_page = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.filter(parent__isnull=True, is_active=True)
    brands = Brand.objects.filter(is_active=True)

    return render(request, 'catalog/catalog.html', {
        'products': products_page,
        'categories': categories,
        'brands': brands,
        'current_brands': current_brands,
        'current_categories': current_categories,
        'brand_slugs': brand_slugs,
        'category_slugs': category_slugs,
        'search_q': search_q,
        'current_sort': sort,
        # backward compat для breadcrumb
        'current_brand': current_brands.first() if brand_slugs else None,
        'current_category': current_categories.first() if category_slugs else None,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images', 'analogues', 'brands', 'car_models'),
        slug=slug, is_active=True
    )
    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk)[:4]
    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'related': related,
    })


def by_brand(request, slug):
    brand = get_object_or_404(Brand, slug=slug, is_active=True)
    products = Product.objects.filter(
        brands=brand, is_active=True
    ).select_related('category').prefetch_related('images')

    sort = request.GET.get('sort', 'popular')
    products = products.order_by(SORT_MAP.get(sort, '-created_at'))

    paginator = Paginator(products, 12)
    products_page = paginator.get_page(request.GET.get('page'))

    return render(request, 'catalog/catalog.html', {
        'products': products_page,
        'current_brand': brand,
        'current_brands': Brand.objects.filter(pk=brand.pk),
        'current_categories': Category.objects.none(),
        'brand_slugs': [brand.slug],
        'category_slugs': [],
        'categories': Category.objects.filter(parent__isnull=True, is_active=True),
        'brands': Brand.objects.filter(is_active=True),
        'search_q': '',
        'current_sort': sort,
    })


def search_suggest(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    results = (
        Product.objects
        .filter(is_active=True)
        .filter(Q(name__icontains=q) | Q(sku__icontains=q))
        .values('name', 'sku', 'slug')[:5]
    )
    return JsonResponse({'results': list(results)})
