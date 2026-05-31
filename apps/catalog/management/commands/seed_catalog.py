from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.catalog.models import Brand, CarModel, Category, Product, Analogue


BRANDS_DATA = [
    {'name': 'КАМАЗ', 'slug': 'kamaz', 'description': 'Камский автомобильный завод', 'order': 1},
    {'name': 'МАЗ', 'slug': 'maz', 'description': 'Минский автомобильный завод', 'order': 2},
    {'name': 'Урал', 'slug': 'ural', 'description': 'Автомобильный завод Урал', 'order': 3},
    {'name': 'КрАЗ', 'slug': 'kraz', 'description': 'Кременчугский автозавод', 'order': 4},
    {'name': 'ЯМЗ', 'slug': 'yamz', 'description': 'Ярославский моторный завод', 'order': 5},
]

CAR_MODELS_DATA = {
    'kamaz': [
        {'name': '65115', 'slug': '65115', 'year_from': 2003},
        {'name': '65117', 'slug': '65117', 'year_from': 2007},
        {'name': '6520', 'slug': '6520', 'year_from': 2002},
        {'name': '5490', 'slug': '5490', 'year_from': 2013},
        {'name': '43118', 'slug': '43118', 'year_from': 1996},
    ],
    'maz': [
        {'name': '5440', 'slug': '5440', 'year_from': 2002},
        {'name': '6501', 'slug': '6501', 'year_from': 2005},
        {'name': '5550', 'slug': '5550', 'year_from': 1995},
    ],
    'ural': [
        {'name': '4320', 'slug': '4320', 'year_from': 1977},
        {'name': '6370', 'slug': '6370', 'year_from': 2007},
    ],
    'kraz': [
        {'name': '255', 'slug': '255', 'year_from': 1967, 'year_to': 1994},
        {'name': '6510', 'slug': '6510', 'year_from': 1994},
    ],
    'yamz': [
        {'name': '238', 'slug': '238', 'year_from': 1965},
        {'name': '536', 'slug': '536', 'year_from': 2010},
    ],
}

CATEGORIES_DATA = [
    {'name': 'Двигатель', 'slug': 'dvigatel', 'icon': 'bi-gear-wide-connected', 'order': 1},
    {'name': 'Трансмиссия', 'slug': 'transmissiya', 'icon': 'bi-gear', 'order': 2},
    {'name': 'Ходовая часть', 'slug': 'hodovaya', 'icon': 'bi-truck', 'order': 3},
    {'name': 'Электрооборудование', 'slug': 'elektro', 'icon': 'bi-lightning-charge', 'order': 4},
    {'name': 'Кузов и кабина', 'slug': 'kuzov', 'icon': 'bi-car-front', 'order': 5},
    {'name': 'Расходные материалы', 'slug': 'rashodni', 'icon': 'bi-droplet', 'order': 6},
    {'name': 'Топливная система', 'slug': 'toplivo', 'icon': 'bi-fuel-pump', 'order': 7},
    {'name': 'Тормозная система', 'slug': 'tormoza', 'icon': 'bi-stop-circle', 'order': 8},
]

PRODUCTS_DATA = [
    # Двигатель
    {
        'name': 'Поршень двигателя КАМАЗ 740.30-1004015',
        'slug': 'porshen-kamaz-740-30-1004015',
        'sku': 'KAM-0001',
        'oem_number': '740.30-1004015',
        'category': 'dvigatel',
        'brands': ['kamaz'],
        'price': Decimal('3850.00'),
        'discount_price': Decimal('3200.00'),
        'stock': 45,
        'is_original': True,
        'is_bestseller': True,
        'is_new': False,
        'description': 'Поршень двигателя КАМАЗ серии 740. Оригинальная запчасть. Диаметр 120 мм.',
        'specifications': 'Диаметр: 120 мм\nМатериал: алюминиевый сплав\nПроизводитель: КАМАЗ\nОригинал: Да',
        'analogues': [('Mahle', 'MC-740'), ('Kolbenschmidt', 'KS-12345')],
    },
    {
        'name': 'Прокладка головки блока цилиндров КАМАЗ 740',
        'slug': 'prokladka-gbc-kamaz-740',
        'sku': 'KAM-0002',
        'oem_number': '740.1003213',
        'category': 'dvigatel',
        'brands': ['kamaz'],
        'price': Decimal('1290.00'),
        'stock': 120,
        'is_original': True,
        'is_bestseller': True,
        'is_new': False,
        'description': 'Прокладка ГБЦ для двигателей КАМАЗ серии 740. Металло-асбестовая.',
        'specifications': 'Тип: металло-асбестовая\nОригинал: Да',
    },
    {
        'name': 'Турбокомпрессор ТКР 7Н1 КАМАЗ 5490',
        'slug': 'turbokompressor-tkr7n1-kamaz',
        'sku': 'KAM-0003',
        'oem_number': 'ТКР 7Н1',
        'category': 'dvigatel',
        'brands': ['kamaz'],
        'price': Decimal('28500.00'),
        'discount_price': Decimal('24900.00'),
        'stock': 8,
        'is_original': False,
        'is_bestseller': False,
        'is_new': True,
        'description': 'Турбокомпрессор ТКР 7Н1 для грузовых автомобилей КАМАЗ. Производство — аналог.',
        'specifications': 'Тип: центробежный\nДавление наддува: 1,5 бар\nОригинал: Нет (аналог)',
        'analogues': [('Garrett', 'GT2256V'), ('BorgWarner', 'BW-14789')],
    },
    {
        'name': 'Фильтр масляный КАМАЗ 740 (MANN)',
        'slug': 'filtr-maslyani-kamaz-mann',
        'sku': 'KAM-0004',
        'oem_number': '740.1012040',
        'category': 'rashodni',
        'brands': ['kamaz'],
        'price': Decimal('890.00'),
        'stock': 200,
        'is_original': False,
        'is_bestseller': True,
        'is_new': False,
        'description': 'Масляный фильтр MANN для двигателей КАМАЗ серии 740.',
        'specifications': 'Резьба: М20х1.5\nВысота: 156 мм\nОригинал: Нет (MANN)',
    },
    # Трансмиссия
    {
        'name': 'КПП КАМАЗ 154 14 ступеней',
        'slug': 'kpp-kamaz-154-14-stupeney',
        'sku': 'KAM-0005',
        'oem_number': '15-4202010',
        'category': 'transmissiya',
        'brands': ['kamaz'],
        'price': Decimal('185000.00'),
        'stock': 3,
        'is_original': True,
        'is_bestseller': False,
        'is_new': True,
        'description': '14-ступенчатая коробка переключения передач КАМАЗ. Оригинальная запчасть.',
        'specifications': 'Количество передач: 14 (7+7R)\nМакс. крутящий момент: 1800 Нм\nМасса: 189 кг',
    },
    {
        'name': 'Диск сцепления КАМАЗ 14" нажимной',
        'slug': 'disk-scepleniya-kamaz-14',
        'sku': 'KAM-0006',
        'oem_number': '142-1601090',
        'category': 'transmissiya',
        'brands': ['kamaz'],
        'price': Decimal('4200.00'),
        'discount_price': Decimal('3750.00'),
        'stock': 35,
        'is_original': True,
        'is_bestseller': True,
        'is_new': False,
        'description': 'Нажимной диск сцепления для КАМАЗ с 14-дюймовым сцеплением.',
        'specifications': 'Диаметр: 14" (355 мм)\nТолщина: 44 мм\nОригинал: Да',
    },
    # Ходовая
    {
        'name': 'Рессора передняя КАМАЗ 65115 (6 листов)',
        'slug': 'ressora-perednyaya-kamaz-65115',
        'sku': 'KAM-0007',
        'oem_number': '65115-2902012',
        'category': 'hodovaya',
        'brands': ['kamaz'],
        'price': Decimal('7800.00'),
        'stock': 18,
        'is_original': True,
        'is_bestseller': False,
        'is_new': False,
        'description': 'Передняя рессора КАМАЗ-65115, 6-листовая. Оригинал.',
        'specifications': 'Количество листов: 6\nДлина: 1490 мм\nМаксимальная нагрузка: 5500 кг',
    },
    {
        'name': 'Ступица передняя КАМАЗ 6520',
        'slug': 'stupica-perednyaya-kamaz-6520',
        'sku': 'KAM-0008',
        'oem_number': '6520-3103015',
        'category': 'hodovaya',
        'brands': ['kamaz'],
        'price': Decimal('12400.00'),
        'stock': 7,
        'is_original': True,
        'is_bestseller': False,
        'is_new': False,
        'description': 'Ступица переднего колеса КАМАЗ-6520 с подшипниками.',
        'specifications': 'PCD: 10x335\nДиаметр отверстия: 281 мм\nОригинал: Да',
    },
    # Тормоза
    {
        'name': 'Тормозные колодки КАМАЗ задние (к-т 8 шт.)',
        'slug': 'tormoznye-kolodki-kamaz-zadnie',
        'sku': 'KAM-0009',
        'oem_number': '5320-3502090',
        'category': 'tormoza',
        'brands': ['kamaz'],
        'price': Decimal('5600.00'),
        'discount_price': Decimal('4900.00'),
        'stock': 40,
        'is_original': False,
        'is_bestseller': True,
        'is_new': False,
        'description': 'Комплект задних тормозных колодок КАМАЗ. 8 штук в комплекте.',
        'specifications': 'Количество в комплекте: 8 шт.\nМатериал накладки: асбестовая смесь\nОригинал: Нет (аналог)',
        'analogues': [('Ferodo', 'FDB4327'), ('TEXTAR', 'TX-2345')],
    },
    # Электро
    {
        'name': 'Стартер КАМАЗ 740 12В (СТ25)',
        'slug': 'starter-kamaz-740-st25',
        'sku': 'KAM-0010',
        'oem_number': 'СТ25-3708000',
        'category': 'elektro',
        'brands': ['kamaz'],
        'price': Decimal('9800.00'),
        'stock': 12,
        'is_original': True,
        'is_bestseller': False,
        'is_new': True,
        'description': 'Стартер 12V для двигателей КАМАЗ 740. Мощность 8,2 кВт.',
        'specifications': 'Напряжение: 12В\nМощность: 8,2 кВт\nТип: планетарный\nОригинал: Да',
    },
    # МАЗ
    {
        'name': 'Двигатель ЯМЗ-536 (МАЗ 5440)',
        'slug': 'dvigatel-yamz-536-maz-5440',
        'sku': 'MAZ-0001',
        'oem_number': '536.1000190',
        'category': 'dvigatel',
        'brands': ['maz', 'yamz'],
        'price': Decimal('420000.00'),
        'stock': 2,
        'is_original': True,
        'is_bestseller': False,
        'is_new': False,
        'description': 'Двигатель ЯМЗ-536 Euro 5 для МАЗ-5440. Мощность 420 л.с.',
        'specifications': 'Мощность: 420 л.с.\nКрутящий момент: 2000 Нм\nЭкологический стандарт: Euro 5\nОбъём: 6,65 л',
    },
    {
        'name': 'Рулевой механизм МАЗ 5550 с усилителем',
        'slug': 'rulevoy-mekhanizm-maz-5550',
        'sku': 'MAZ-0002',
        'oem_number': '5550-3400020',
        'category': 'hodovaya',
        'brands': ['maz'],
        'price': Decimal('31500.00'),
        'stock': 5,
        'is_original': True,
        'is_bestseller': False,
        'is_new': False,
        'description': 'Рулевой механизм МАЗ с гидроусилителем.',
        'specifications': 'Передаточное число: 22,3\nОригинал: Да',
    },
    # Урал
    {
        'name': 'Мост передний ведущий Урал-4320',
        'slug': 'most-peredniy-ural-4320',
        'sku': 'URA-0001',
        'oem_number': '375-2300010',
        'category': 'transmissiya',
        'brands': ['ural'],
        'price': Decimal('78000.00'),
        'stock': 4,
        'is_original': True,
        'is_bestseller': False,
        'is_new': False,
        'description': 'Передний ведущий мост для Урал-4320. В сборе.',
        'specifications': 'Передаточное число: 7,32\nМакс. нагрузка: 5500 кг\nОригинал: Да',
    },
    # Расходники
    {
        'name': 'Фильтр воздушный КАМАЗ 740 (MANN C30850)',
        'slug': 'filtr-vozdushniy-kamaz-mann',
        'sku': 'KAM-0011',
        'oem_number': '740.1109560',
        'category': 'rashodni',
        'brands': ['kamaz'],
        'price': Decimal('1450.00'),
        'discount_price': Decimal('1190.00'),
        'stock': 85,
        'is_original': False,
        'is_bestseller': True,
        'is_new': False,
        'description': 'Воздушный фильтр MANN для КАМАЗ 740. Сухой тип.',
        'specifications': 'Тип: сухой\nДиаметр входного патрубка: 100 мм\nОригинал: Нет (MANN)',
        'analogues': [('KAMAZ', '740.1109560'), ('Fleetguard', 'AF4561')],
    },
    {
        'name': 'Ремень ГРМ КАМАЗ 740 Евро (к-т)',
        'slug': 'remen-grm-kamaz-740-evro',
        'sku': 'KAM-0012',
        'oem_number': '740.60-1006040',
        'category': 'rashodni',
        'brands': ['kamaz'],
        'price': Decimal('3200.00'),
        'stock': 60,
        'is_original': True,
        'is_bestseller': False,
        'is_new': True,
        'description': 'Комплект ремня привода распределительного вала для КАМАЗ 740 Евро.',
        'specifications': 'Количество зубьев: 136\nШирина: 30 мм\nОригинал: Да',
    },
    # Топливная
    {
        'name': 'ТНВД КАМАЗ 740 (BOSCH 0445020119)',
        'slug': 'tnvd-kamaz-740-bosch',
        'sku': 'KAM-0013',
        'oem_number': '0445020119',
        'category': 'toplivo',
        'brands': ['kamaz'],
        'price': Decimal('68500.00'),
        'discount_price': Decimal('61000.00'),
        'stock': 6,
        'is_original': False,
        'is_bestseller': False,
        'is_new': True,
        'description': 'Топливный насос высокого давления BOSCH для КАМАЗ 740 Euro 4/5.',
        'specifications': 'Производитель: BOSCH\nТип: Common Rail\nОригинал: Нет (BOSCH OEM)',
    },
    {
        'name': 'Форсунка топливная КАМАЗ BOSCH 0445120231',
        'slug': 'forsunka-kamaz-bosch-0445120231',
        'sku': 'KAM-0014',
        'oem_number': '0445120231',
        'category': 'toplivo',
        'brands': ['kamaz'],
        'price': Decimal('14800.00'),
        'stock': 24,
        'is_original': False,
        'is_bestseller': True,
        'is_new': False,
        'description': 'Форсунка Common Rail BOSCH для двигателей КАМАЗ Euro 4.',
        'specifications': 'Производитель: BOSCH\nТип: электромагнитная\nОригинал: Нет (BOSCH OEM)',
        'analogues': [('Delphi', 'EJBR04201D'), ('Denso', 'DCRI109960')],
    },
    # Кузов
    {
        'name': 'Дверь кабины левая КАМАЗ 5490',
        'slug': 'dver-kabiny-levaya-kamaz-5490',
        'sku': 'KAM-0015',
        'oem_number': '5490-6101011',
        'category': 'kuzov',
        'brands': ['kamaz'],
        'price': Decimal('42000.00'),
        'stock': 3,
        'is_original': True,
        'is_bestseller': False,
        'is_new': False,
        'description': 'Дверь кабины водителя (левая) для КАМАЗ-5490 Neo. В сборе с механизмами.',
        'specifications': 'Сторона: левая\nКомплектация: в сборе\nОригинал: Да',
    },
    {
        'name': 'Буфер передний КАМАЗ 6520 (нижний)',
        'slug': 'bufer-peredniy-kamaz-6520',
        'sku': 'KAM-0016',
        'oem_number': '6520-8407012',
        'category': 'kuzov',
        'brands': ['kamaz'],
        'price': Decimal('5400.00'),
        'discount_price': Decimal('4650.00'),
        'stock': 15,
        'is_original': True,
        'is_bestseller': False,
        'is_new': False,
        'description': 'Нижний передний бампер КАМАЗ-6520.',
        'specifications': 'Позиция: нижний\nМатериал: пластик ABS\nОригинал: Да',
    },
    # КрАЗ
    {
        'name': 'Редуктор среднего моста КрАЗ-6510',
        'slug': 'reduktor-srednego-mosta-kraz-6510',
        'sku': 'KRZ-0001',
        'oem_number': '6510-2402010',
        'category': 'transmissiya',
        'brands': ['kraz'],
        'price': Decimal('54000.00'),
        'stock': 2,
        'is_original': True,
        'is_bestseller': False,
        'is_new': False,
        'description': 'Редуктор среднего ведущего моста КрАЗ-6510.',
        'specifications': 'Передаточное число: 6,55\nОригинал: Да',
    },
]


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми товарами для разработки'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Очистить данные перед заполнением')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Очистка данных каталога...')
            Analogue.objects.all().delete()
            Product.objects.all().delete()
            CarModel.objects.all().delete()
            Category.objects.all().delete()
            Brand.objects.all().delete()

        # Бренды
        self.stdout.write('Создание марок...')
        brands = {}
        for data in BRANDS_DATA:
            brand, created = Brand.objects.update_or_create(
                slug=data['slug'],
                defaults=data,
            )
            brands[data['slug']] = brand
            if created:
                self.stdout.write(f'  + {brand.name}')

        # Модели автомобилей
        self.stdout.write('Создание моделей...')
        for brand_slug, models in CAR_MODELS_DATA.items():
            brand = brands[brand_slug]
            for m in models:
                CarModel.objects.update_or_create(
                    brand=brand,
                    slug=m['slug'],
                    defaults={**m, 'brand': brand},
                )

        # Категории
        self.stdout.write('Создание категорий...')
        categories = {}
        for data in CATEGORIES_DATA:
            cat, created = Category.objects.update_or_create(
                slug=data['slug'],
                defaults=data,
            )
            categories[data['slug']] = cat
            if created:
                self.stdout.write(f'  + {cat.name}')

        # Товары
        self.stdout.write('Создание товаров...')
        for data in PRODUCTS_DATA:
            analogues = data.pop('analogues', [])
            brand_slugs = data.pop('brands', [])
            cat_slug = data.pop('category')
            data.pop('specifications', None)  # поле удалено из модели

            product, created = Product.objects.update_or_create(
                sku=data['sku'],
                defaults={
                    **data,
                    'category': categories[cat_slug],
                },
            )
            product.brands.set([brands[s] for s in brand_slugs if s in brands])

            if created:
                for brand_name, part_number in analogues:
                    Analogue.objects.get_or_create(
                        product=product,
                        brand_name=brand_name,
                        part_number=part_number,
                    )
                self.stdout.write(f'  + {product.sku} — {product.name[:50]}')

        total = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\nГотово! Товаров в БД: {total}'))
