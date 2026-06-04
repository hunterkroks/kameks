from django.core.cache import cache
from .models import Category


def menu_categories(request):
    menu_cats = cache.get('menu_cats_v1')
    if menu_cats is None:
        menu_cats = list(
            Category.objects
            .filter(parent__isnull=True, is_active=True)
            .prefetch_related('children__children')
            .order_by('order')
        )
        cache.set('menu_cats_v1', menu_cats, 60 * 60)
    return {'menu_cats': menu_cats}
