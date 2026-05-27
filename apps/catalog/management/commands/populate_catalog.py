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


class Command(BaseCommand):
    help = 'Загружает начальные данные каталога если БД пуста'

    def handle(self, *args, **options):
        # 1. Создаём категории и бренды если их ещё нет
        if not Category.objects.exists() or not Brand.objects.filter(is_active=True).exists():
            self.stdout.write('Создаю категории и бренды...')
            call_command('seed_catalog')

        # 2. Импортируем товары из CSV если реальных товаров ещё нет
        csv_products = Product.objects.filter(sku__startswith='CSV-').count()
        if csv_products:
            self.stdout.write(f'[skip] CSV-товары уже импортированы ({csv_products} шт.)')
        else:
            csv_path = Path(settings.BASE_DIR) / 'fixtures' / 'price_kameks.csv'
            if csv_path.exists():
                test_count = Product.objects.exclude(sku__startswith='CSV-').count()
                if test_count:
                    Product.objects.exclude(sku__startswith='CSV-').delete()
                    self.stdout.write(f'Удалено {test_count} тестовых товаров')

                self.stdout.write('Импортирую товары из price_kameks.csv...')
                call_command('import_csv', str(csv_path))
                total = Product.objects.count()
                self.stdout.write(self.style.SUCCESS(f'[OK] Импортировано {total} товаров'))

                # Помечаем первые 8 как хиты, следующие 8 как новинки
                bestseller_ids = list(
                    Product.objects.filter(sku__startswith='CSV-', is_active=True)
                    .order_by('id')[:8].values_list('id', flat=True)
                )
                new_ids = list(
                    Product.objects.filter(sku__startswith='CSV-', is_active=True)
                    .exclude(id__in=bestseller_ids)
                    .order_by('id')[:8].values_list('id', flat=True)
                )
                Product.objects.filter(id__in=bestseller_ids).update(is_bestseller=True)
                Product.objects.filter(id__in=new_ids).update(is_new=True)
                self.stdout.write(f'[OK] Помечено {len(bestseller_ids)} хитов, {len(new_ids)} новинок')
            else:
                self.stdout.write(self.style.WARNING('[warn] fixtures/price_kameks.csv не найден'))

        # 3. Копируем фото категорий в media/ и прописываем пути в БД
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
                # Прописываем путь в БД (идемпотентно)
                Category.objects.filter(slug=slug).update(image=f'categories/{filename}')
            self.stdout.write(self.style.SUCCESS('[OK] Фото категорий назначены'))
