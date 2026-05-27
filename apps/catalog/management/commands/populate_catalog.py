import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from apps.catalog.models import Product, Category


class Command(BaseCommand):
    help = 'Загружает начальные данные каталога если БД пуста'

    def handle(self, *args, **options):
        # 1. Создаём категории и бренды если их ещё нет
        if not Category.objects.exists():
            self.stdout.write('Создаю категории и бренды...')
            call_command('seed_catalog')

        # 2. Импортируем товары из CSV если реальных товаров ещё нет
        csv_products = Product.objects.filter(sku__startswith='CSV-').count()
        if csv_products:
            self.stdout.write(f'[skip] CSV-товары уже импортированы ({csv_products} шт.)')
        else:
            csv_path = Path(settings.BASE_DIR) / 'fixtures' / 'price_kameks.csv'
            if csv_path.exists():
                # Удаляем тестовые/сидовые товары перед импортом реальных
                test_count = Product.objects.exclude(sku__startswith='CSV-').count()
                if test_count:
                    Product.objects.exclude(sku__startswith='CSV-').delete()
                    self.stdout.write(f'Удалено {test_count} тестовых товаров')

                self.stdout.write('Импортирую товары из price_kameks.csv...')
                call_command('import_csv', str(csv_path))
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] Импортировано {Product.objects.count()} товаров'
                ))
            else:
                self.stdout.write(self.style.WARNING('[warn] fixtures/price_kameks.csv не найден'))

        # 3. Копируем фото категорий в media/ если их нет
        src_dir = Path(settings.BASE_DIR) / 'initial_media' / 'categories'
        dst_dir = Path(settings.MEDIA_ROOT) / 'categories'
        if src_dir.exists():
            dst_dir.mkdir(parents=True, exist_ok=True)
            copied = 0
            for src in src_dir.iterdir():
                dst = dst_dir / src.name
                if not dst.exists():
                    shutil.copy2(src, dst)
                    copied += 1
            if copied:
                self.stdout.write(self.style.SUCCESS(f'[OK] Скопировано {copied} фото категорий'))
            else:
                self.stdout.write('[skip] Фото категорий уже на месте')
