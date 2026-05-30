from .models import Category


def menu_categories(request):
    cats = (
        Category.objects
        .filter(parent__isnull=True, is_active=True)
        .prefetch_related('children__children')
        .order_by('order')
    )
    return {'menu_cats': cats}
