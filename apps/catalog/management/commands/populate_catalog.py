import re
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from apps.catalog.models import Product, Category, Brand

CATEGORY_IMAGES = {
    'dvigatel':     '4310-3122035.jpg',
    'transmissiya': '3202.3771000.jpg',
    'hodovaya':     '24-2904000-01.jpg',
    'elektro':      '6001.3701.jpg',
    'kuzov':        'kamaz.jpg',
    'rashodni':     '453479.005.jpg',
    'toplivo':      '5320-1109250.jpg',
    'tormoza':      '100-3521010.jpg',
}

MAIN_BRANDS = [
    {'name': 'КАМАЗ',  'slug': 'kamaz',  'order': 1},
    {'name': 'МАЗ',    'slug': 'maz',    'order': 2},
    {'name': 'Урал',   'slug': 'ural',   'order': 3},
    {'name': 'КрАЗ',   'slug': 'kraz',   'order': 4},
    {'name': 'ЯМЗ',    'slug': 'yamz',   'order': 5},
    {'name': 'ЗИЛ',    'slug': 'zil',    'order': 10},
    {'name': 'ЛиАЗ',   'slug': 'liaz',   'order': 11},
    {'name': 'НЕФАЗ',  'slug': 'nefaz',  'order': 12},
    {'name': 'Икарус', 'slug': 'ikarus', 'order': 13},
    {'name': 'ГАЗ',    'slug': 'gaz',    'order': 14},
    {'name': 'МТЗ',    'slug': 'mtz',    'order': 15},
]

# SKU-паттерны тестовых товаров из seed_catalog
_TEST_SKU_RE = re.compile(r'^(KAM|MAZ|URA|KRZ)-\d+$')


def _is_real_catalog(total: int) -> bool:
    """Реальные данные из CSV — более 50 позиций."""
    return total > 50


class Command(BaseCommand):
    help = 'Загружает начальные данные каталога если БД пуста'

    def handle(self, *args, **options):
        # 1. Создаём категории если их ещё нет
        if not Category.objects.exists():
            self.stdout.write('Создаю категории и бренды через seed_catalog...')
            call_command('seed_catalog')

        # 2. Всегда гарантируем что основные марки существуют и активны
        for bd in MAIN_BRANDS:
            Brand.objects.update_or_create(
                slug=bd['slug'],
                defaults={'name': bd['name'], 'order': bd['order'], 'is_active': True},
            )
        self.stdout.write('[OK] Марки автомобилей в порядке')

        # 3. Убираем префикс CSV- из артикулов (одноразовая очистка)
        prefixed = list(Product.objects.filter(sku__startswith='CSV-').values('pk', 'sku'))
        if prefixed:
            clean_skus = set(
                Product.objects.exclude(sku__startswith='CSV-').values_list('sku', flat=True)
            )
            fixed = 0
            for row in prefixed:
                new_sku = row['sku'][4:]
                if new_sku not in clean_skus:
                    Product.objects.filter(pk=row['pk']).update(sku=new_sku)
                    clean_skus.add(new_sku)
                    fixed += 1
            if fixed:
                self.stdout.write(self.style.SUCCESS(f'[OK] Убраны префиксы CSV- у {fixed} артикулов'))

        # 4. Импортируем товары из CSV если реального каталога ещё нет
        total = Product.objects.count()
        if _is_real_catalog(total):
            self.stdout.write(f'[skip] Каталог уже заполнен ({total} товаров)')
        else:
            csv_path = Path(settings.BASE_DIR) / 'fixtures' / 'price_kameks.csv'
            if csv_path.exists():
                # Удаляем тестовые товары seed_catalog
                test_qs = Product.objects.filter(
                    sku__in=[p.sku for p in Product.objects.all()
                              if _TEST_SKU_RE.match(p.sku)]
                )
                test_count = test_qs.count()
                if test_count:
                    test_qs.delete()
                    self.stdout.write(f'Удалено {test_count} тестовых товаров')

                self.stdout.write('Импортирую товары из price_kameks.csv...')
                call_command('import_csv', str(csv_path))
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] Импортировано {Product.objects.count()} товаров'
                ))
            else:
                self.stdout.write(self.style.WARNING('[warn] fixtures/price_kameks.csv не найден'))

        # 5. Помечаем хиты и новинки — всегда, если их ещё нет
        if not Product.objects.filter(is_bestseller=True).exists():
            ids = list(
                Product.objects.filter(is_active=True).order_by('id')[:8]
                .values_list('id', flat=True)
            )
            if ids:
                Product.objects.filter(id__in=ids).update(is_bestseller=True)
                self.stdout.write(f'[OK] Помечено {len(ids)} хитов продаж')

        if not Product.objects.filter(is_new=True).exists():
            ids = list(
                Product.objects.filter(is_active=True, is_bestseller=False)
                .order_by('id')[:8].values_list('id', flat=True)
            )
            if ids:
                Product.objects.filter(id__in=ids).update(is_new=True)
                self.stdout.write(f'[OK] Помечено {len(ids)} новинок')

        # 6. Копируем фото категорий в media/ и прописываем пути в БД
        src_dir = Path(settings.BASE_DIR) / 'initial_media' / 'categories'
        dst_dir = Path(settings.MEDIA_ROOT) / 'categories'
        if src_dir.exists():
            dst_dir.mkdir(parents=True, exist_ok=True)
            for slug, filename in CATEGORY_IMAGES.items():
                src = src_dir / filename
                if not src.exists():
                    continue
                dst = dst_dir / filename
                if not dst.exists():
                    shutil.copy2(src, dst)
                Category.objects.filter(slug=slug).update(image=f'categories/{filename}')
            self.stdout.write(self.style.SUCCESS('[OK] Фото категорий назначены'))
