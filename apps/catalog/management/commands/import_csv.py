"""
Импорт прайс-листа КАМЭКС из CSV (кодировка Windows-1251).

Использование:
    python manage.py import_csv "C:/path/to/price.csv"
    python manage.py import_csv "C:/path/to/price.csv" --clear
"""
import csv
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from apps.catalog.models import Brand, Category, Product, Analogue

# Карта: ключевые слова из заголовка секции → slug категории
SECTION_MAP = {
    'амортизатор': 'hodovaya',
    'домкрат': 'hodovaya',
    'батэ': 'elektro',
    'вал карданный': 'transmissiya',
    'валы карданные': 'transmissiya',
    'карданы': 'transmissiya',
    'вкладыш': 'dvigatel',
    'генератор': 'elektro',
    'гур': 'hodovaya',
    'насос гур': 'hodovaya',
    'нш': 'hodovaya',
    'датчик': 'elektro',
    'запчасти камаз': 'rashodni',
    'зит': 'elektro',
    'компрессор': 'tormoza',
    'крестовин': 'transmissiya',
    'оптика': 'kuzov',
    'рти': 'rashodni',
    'стартер': 'elektro',
    'тормозная': 'tormoza',
    'фитинг': 'rashodni',
    'шланги': 'rashodni',
    'шааз': 'dvigatel',
    'элементы фильтров': 'rashodni',
    'энергомаш': 'elektro',
    'другие': 'rashodni',
    'прамо': 'elektro',
    'пааз': 'tormoza',
    'рааз': 'tormoza',
    'sorl': 'tormoza',
    'автокомпонент': 'tormoza',
}

# Для автодетекции категории из названия товара (раздел "Запчасти КАМАЗ")
NAME_CATEGORY_MAP = {
    'насос масл': 'dvigatel',
    'поршн': 'dvigatel',
    'прокладка': 'dvigatel',
    'кольца поршн': 'dvigatel',
    'кольцо маслонаг': 'dvigatel',
    'натяжитель': 'dvigatel',
    'ремень': 'dvigatel',
    'экран': 'dvigatel',
    'вал промеж': 'transmissiya',
    'муфта': 'transmissiya',
    'вилка пер': 'transmissiya',
    'вилка флан': 'transmissiya',
    'воздухорас': 'transmissiya',
    'стакан подшип': 'transmissiya',
    'чашки мод': 'transmissiya',
    'рессора': 'hodovaya',
    'амортиз': 'hodovaya',
    'тяга продольн': 'hodovaya',
    'тяга рулев': 'hodovaya',
    'колодка тормозн': 'tormoza',
    'ролик тормоз': 'tormoza',
    'накладка оси тормоз': 'tormoza',
    'чека': 'tormoza',
    'стартер': 'elektro',
    'генератор': 'elektro',
    'гнездо акб': 'elektro',
    'замок зажиг': 'elektro',
    'панель облиц': 'kuzov',
    'панель передка': 'kuzov',
    'панель с обтек': 'kuzov',
    'буфер': 'kuzov',
}

# Бренды — ключевые слова для поиска в названии товара
BRAND_KEYWORDS = {
    'kamaz': ['камаз'],
    'maz': ['маз'],
    'ural': ['урал'],
    'kraz': ['краз'],
    'yamz': ['ямз'],
}

# Бренды из других единиц техники — создадим, но с is_active=False
EXTRA_BRANDS = [
    {'name': 'ЗИЛ', 'slug': 'zil', 'order': 10, 'is_active': False},
    {'name': 'ЛиАЗ', 'slug': 'liaz', 'order': 11, 'is_active': False},
    {'name': 'НЕФАЗ', 'slug': 'nefaz', 'order': 12, 'is_active': False},
    {'name': 'Икарус', 'slug': 'ikarus', 'order': 13, 'is_active': False},
    {'name': 'ГАЗ', 'slug': 'gaz', 'order': 14, 'is_active': False},
    {'name': 'МТЗ', 'slug': 'mtz', 'order': 15, 'is_active': False},
]
EXTRA_BRAND_KEYWORDS = {
    'zil': ['зил'],
    'liaz': ['лиаз'],
    'nefaz': ['нефаз'],
    'ikarus': ['икарус'],
    'gaz': [' газ-', ' газ ', 'гаэль'],
    'mtz': ['мтз'],
}

TRANSLIT_MAP = str.maketrans({
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh',
    'з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o',
    'п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh','ц':'ts',
    'ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    'А':'a','Б':'b','В':'v','Г':'g','Д':'d','Е':'e','Ё':'yo','Ж':'zh',
    'З':'z','И':'i','Й':'y','К':'k','Л':'l','М':'m','Н':'n','О':'o',
    'П':'p','Р':'r','С':'s','Т':'t','У':'u','Ф':'f','Х':'kh','Ц':'ts',
    'Ч':'ch','Ш':'sh','Щ':'sch','Ъ':'','Ы':'y','Ь':'','Э':'e','Ю':'yu','Я':'ya',
})


def translit(text):
    return text.translate(TRANSLIT_MAP)


def make_slug(sku, name=''):
    raw = sku.strip() if sku.strip() else name
    raw = re.sub(r'\([^)]*\)', '', raw)
    raw = translit(raw)
    raw = re.sub(r'[^a-zA-Z0-9\-]', '-', raw)
    raw = re.sub(r'-+', '-', raw).strip('-').lower()
    return raw[:80] or 'product'


def parse_price(raw):
    raw = re.sub(r'[^\d,]', '', raw.replace(' ', ''))
    raw = raw.replace(',', '.')
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def detect_category(name_lower, section_slug, categories_cache):
    """Пытается уточнить категорию по ключевым словам в названии."""
    for keyword, slug in NAME_CATEGORY_MAP.items():
        if keyword in name_lower and slug in categories_cache:
            return categories_cache[slug]
    return categories_cache.get(section_slug)


def detect_brands(name_lower, brands_cache):
    found = []
    all_keywords = {**BRAND_KEYWORDS, **EXTRA_BRAND_KEYWORDS}
    for slug, keywords in all_keywords.items():
        if slug in brands_cache:
            for kw in keywords:
                if kw in name_lower:
                    found.append(brands_cache[slug])
                    break
    return found


def section_to_category_slug(header_lower):
    for kw, slug in SECTION_MAP.items():
        if kw in header_lower:
            return slug
    return None


class Command(BaseCommand):
    help = 'Импортирует прайс-лист из CSV файла (кодировка cp1251)'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Путь к CSV файлу')
        parser.add_argument('--clear', action='store_true', help='Удалить ранее импортированные товары перед импортом')
        parser.add_argument('--dry-run', action='store_true', help='Только показать что будет импортировано')
        parser.add_argument('--stock', type=int, default=10, help='Количество на складе для новых товаров (по умолч. 10)')

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])
        if not csv_path.exists():
            raise CommandError(f'Файл не найден: {csv_path}')

        dry_run = options['dry_run']
        default_stock = options['stock']

        # --- Создать дополнительные бренды ---
        if not dry_run:
            for bd in EXTRA_BRANDS:
                Brand.objects.get_or_create(slug=bd['slug'], defaults={
                    'name': bd['name'], 'order': bd['order'], 'is_active': bd['is_active']
                })

        brands_cache = {b.slug: b for b in Brand.objects.all()}
        categories_cache = {c.slug: c for c in Category.objects.all()}

        if not categories_cache:
            raise CommandError('Категории не найдены. Сначала выполните: python manage.py seed_catalog')

        if options['clear'] and not dry_run:
            deleted = Product.objects.filter(sku__startswith='CSV-').delete()
            self.stdout.write(f'Удалено {deleted[0]} товаров с префиксом CSV-')

        # --- Разбор CSV ---
        created_count = 0
        skipped_count = 0
        current_category_slug = 'rashodni'  # fallback
        current_section_name = ''
        auto_seq = 1
        existing_slugs = set(Product.objects.values_list('slug', flat=True))
        existing_skus = set(Product.objects.values_list('sku', flat=True))

        for enc in ('cp1251', 'utf-8-sig', 'utf-8'):
            try:
                with open(csv_path, encoding=enc) as probe:
                    probe.read(512)
                chosen_enc = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            chosen_enc = 'cp1251'

        self.stdout.write(f'Кодировка: {chosen_enc}')

        with open(csv_path, encoding=chosen_enc, newline='') as f:
            reader = csv.reader(f, delimiter=';')
            data_started = False

            for row_num, row in enumerate(reader, 1):
                if len(row) < 2:
                    continue

                col_sku = row[0].strip()
                col_name = row[1].strip()
                col_price = row[2].strip() if len(row) > 2 else ''
                col_unit = row[3].strip() if len(row) > 3 else ''

                # Пропускаем заголовочные строки до первой секции
                if not data_started:
                    if col_sku == '' and col_price == '' and col_name and 'руб' not in col_price:
                        header_low = col_name.lower()
                        cat_slug = section_to_category_slug(header_low)
                        if cat_slug:
                            data_started = True
                            current_category_slug = cat_slug
                            current_section_name = col_name
                            self.stdout.write(f'\n[Секция] {col_name} -> {cat_slug}')
                    continue

                # Строка — заголовок секции (нет артикула, нет цены)
                if col_sku == '' and col_price == '':
                    if col_name:
                        header_low = col_name.lower()
                        cat_slug = section_to_category_slug(header_low)
                        if cat_slug:
                            current_category_slug = cat_slug
                            current_section_name = col_name
                            self.stdout.write(f'\n[Секция] {col_name} -> {cat_slug}')
                    continue

                # Строка — товар (есть цена)
                if 'руб' not in col_price and col_price != '':
                    continue
                if not col_price or 'руб' not in col_price:
                    continue

                price = parse_price(col_price)
                if price is None or price <= 0:
                    skipped_count += 1
                    continue

                name = col_name.strip('"').strip()
                if not name or len(name) < 3:
                    skipped_count += 1
                    continue

                # SKU
                sku_raw = col_sku if col_sku else f'AUTO-{auto_seq:04d}'
                if not col_sku:
                    auto_seq += 1
                sku = f'CSV-{sku_raw}'[:100]

                # Slug
                base_slug = make_slug(col_sku, name)
                slug = base_slug
                counter = 1
                while slug in existing_slugs:
                    slug = f'{base_slug}-{counter}'
                    counter += 1

                # Категория
                name_lower = name.lower()
                if 'запчасти камаз' in current_section_name.lower():
                    category = detect_category(name_lower, current_category_slug, categories_cache)
                else:
                    category = categories_cache.get(current_category_slug)

                if category is None:
                    category = categories_cache.get('rashodni') or list(categories_cache.values())[0]

                # Бренды
                found_brands = detect_brands(name_lower, brands_cache)

                # Описание
                description = f'{name}. Производитель: {current_section_name}.'

                if dry_run:
                    self.stdout.write(f'  [DRY] {sku} | {name[:50]} | {price} ₽ | {category.slug}')
                    created_count += 1
                    existing_slugs.add(slug)
                    continue

                if sku in existing_skus:
                    skipped_count += 1
                    continue

                product = Product.objects.create(
                    sku=sku,
                    slug=slug,
                    name=name,
                    description=description,
                    price=price,
                    stock=default_stock,
                    category=category,
                    is_original=False,
                    is_active=True,
                    is_bestseller=False,
                    is_new=False,
                )
                product.brands.set(found_brands)
                existing_slugs.add(slug)
                existing_skus.add(sku)
                created_count += 1

                if created_count % 50 == 0:
                    self.stdout.write(f'  ... создано {created_count} товаров')

        mode = '[DRY RUN]' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(
            f'\n{mode} Готово! Создано: {created_count}, пропущено: {skipped_count}'
        ))
