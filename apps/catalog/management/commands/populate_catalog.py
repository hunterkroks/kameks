import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from apps.catalog.models import Product


class Command(BaseCommand):
    help = 'Загружает начальные данные каталога если БД пуста'

    def handle(self, *args, **options):
        # 1. Загружаем фикстуру если товаров нет
        if Product.objects.exists():
            self.stdout.write('[skip] Данные уже есть, пропускаем loaddata')
        else:
            fixture = Path(settings.BASE_DIR) / 'fixtures' / 'catalog_data.json'
            if fixture.exists():
                self.stdout.write('Загружаю fixtures/catalog_data.json...')
                call_command('loaddata', str(fixture))
                self.stdout.write(self.style.SUCCESS(
                    f'[OK] Загружено {Product.objects.count()} товаров'
                ))
            else:
                self.stdout.write(self.style.WARNING('[warn] fixtures/catalog_data.json не найден'))

        # 2. Копируем фото категорий в media/ если их нет
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
