import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.catalog.models import Category

# Маппинг: slug категории -> файл из downloaded_images
# Подбор по паттернам номеров запчастей КАМАЗ:
# .3701 = генераторы; .3708 = стартеры; 100-35xx = тормоза
# 3202/3212.3771 = карданные валы; 3407 = рулевое управление
# 5320-1xxx = двигатель; 5320-1109 = топливная система
# 453xxx (SORL) = РТИ/уплотнители -> расходные материалы
MAPPING = {
    'dvigatel':    '4310-3122035.jpg',   # крепёж блока двигателя
    'transmissiya':'3202.3771000.jpg',   # карданный вал (3771 = трансмиссия)
    'hodovaya':    '24-2904000-01.jpg',  # передняя ось / подвеска
    'elektro':     '6001.3701.jpg',      # генератор Г-6001 (21 KB, лучшее фото)
    'kuzov':       'kamaz.jpg',          # грузовой автомобиль КАМАЗ
    'rashodni':    '453479.005.jpg',     # РТИ/уплотнитель SORL
    'toplivo':     '5320-1109250.jpg',   # трубка топливной системы
    'tormoza':     '100-3521010.jpg',    # тормозная аппаратура (100-35xx)
}


class Command(BaseCommand):
    help = 'Копирует фото категорий из downloaded_images в media/categories/ и назначает их категориям'

    def handle(self, *args, **options):
        src_dir = Path(settings.BASE_DIR) / 'downloaded_images'
        dst_dir = Path(settings.MEDIA_ROOT) / 'categories'
        dst_dir.mkdir(parents=True, exist_ok=True)

        for slug, filename in MAPPING.items():
            src = src_dir / filename
            if not src.exists():
                self.stdout.write(f'[SKIP] {filename} - файл не найден в downloaded_images')
                continue

            dst = dst_dir / filename
            shutil.copy2(src, dst)

            cat = Category.objects.filter(slug=slug).first()
            if not cat:
                self.stdout.write(f'[SKIP] Категория slug={slug} не найдена в БД')
                continue

            cat.image = f'categories/{filename}'
            cat.save(update_fields=['image'])
            self.stdout.write(f'[OK] {cat.name} -> categories/{filename}')

        self.stdout.write(self.style.SUCCESS('Готово!'))
