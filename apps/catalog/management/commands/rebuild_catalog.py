import csv
import os
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import Brand, Category, Product


class Command(BaseCommand):
    help = 'Пересоздать каталог: категории + марки + импорт товаров из fixtures/kameks_catalog.csv'

    CSV_PATH = os.path.join('fixtures', 'kameks_catalog.csv')

    TREE = [
        ('Ходовая часть', 'hodovaya', 'bi-car-front', 1, [
            ('Амортизаторы', 'amortizatory', 1, [
                ('Амортизаторы подвески', 'amort-podveski'),
                ('Амортизаторы кабины',  'amort-kabiny'),
                ('Амортизаторы сиденья', 'amort-sidenya'),
            ]),
            ('Рессоры и детали', 'ressory', 2, [
                ('Рессоры',   'ressory-list'),
                ('Стремянки', 'stremyanki'),
            ]),
            ('Реактивные штанги', 'reaktivnye-shtangi', 3, [
                ('Вкладыши штанг', 'vkladyshi-shtang'),
            ]),
            ('Домкраты', 'domkraty', 4, [
                ('Домкраты', 'domkraty-list'),
            ]),
        ]),
        ('Трансмиссия', 'transmissiya', 'bi-gear', 2, [
            ('Валы карданные', 'valy-kardannye', 1, [
                ('Валы карданные КАМАЗ', 'valy-kamaz'),
                ('Валы карданные МАЗ',  'valy-maz'),
                ('Валы карданные КрАЗ', 'valy-kraz'),
                ('Валы карданные Урал', 'valy-ural'),
            ]),
            ('Крестовины', 'krestoviny', 2, [
                ('Крестовины карданные', 'krestoviny-list'),
            ]),
            ('Вкладыши и втулки', 'vkladyshi', 3, [
                ('Вкладыши коренные',  'vkladyshi-korennye'),
                ('Вкладыши шатунные',  'vkladyshi-shatunnye'),
                ('Втулки распредвала', 'vtulki-raspredvala'),
            ]),
            ('КПП и сцепление', 'kpp', 4, [
                ('Детали КПП', 'detali-kpp'),
            ]),
            ('Мосты и балансиры', 'mosty', 5, [
                ('Детали мостов', 'detali-mostov'),
                ('Шланги МОД',    'shlangi-mod'),
            ]),
        ]),
        ('Тормозная система', 'tormoza', 'bi-record-circle', 3, [
            ('Тормозная аппаратура', 'torm-apparatura', 1, [
                ('Головки соединительные',      'golovki-palm'),
                ('Клапаны',                     'klapany'),
                ('Влагоотделители',             'vlagootdeliteli'),
                ('Энергоаккумуляторы',          'energoakkumulyatory'),
                ('Регуляторы тормозных сил',    'regulyatory-torm'),
                ('Тормозная аппаратура прочее', 'torm-apparatura-prochee'),
            ]),
            ('Тормозные камеры', 'torm-kamery', 2, [
                ('Камеры тормозные', 'kamery-list'),
            ]),
            ('Компрессоры', 'kompressory', 3, [
                ('Компрессоры тормозные', 'komp-list'),
            ]),
            ('Тормозные колодки', 'torm-kolodki', 4, [
                ('Колодки и накладки', 'kolodki-list'),
            ]),
        ]),
        ('Двигатель', 'dvigatel', 'bi-engine', 4, [
            ('Прокладки и уплотнения', 'prokladki', 1, [
                ('Прокладки головки блока',    'prokladki-gbts'),
                ('Прокладки клапанной крышки', 'prokladki-klapan'),
                ('Прокладки коллектора',       'prokladki-kollektor'),
                ('Манжеты и сальники',         'manzhety'),
                ('РТИ и уплотнения',           'rti'),
                ('Прокладки прочие',           'prokladki-prochie'),
            ]),
            ('Фильтры', 'filtry', 2, [
                ('Фильтры масляные',  'filtry-maslo'),
                ('Фильтры топливные', 'filtry-toplivo'),
                ('Фильтры воздушные', 'filtry-vozdukh'),
                ('Воздухозаборники',  'vozdukhozaborniki'),
            ]),
            ('Детали ЦПГ', 'tspg', 3, [
                ('Поршневые кольца', 'porshnevye-kolca'),
                ('Гильзы цилиндров', 'gilzy'),
                ('Поршневая группа', 'porshnevaya'),
                ('Детали маховика',  'makhodik'),
            ]),
            ('Система охлаждения', 'okhlazhdenie', 4, [
                ('Радиаторы',                    'radiatory'),
                ('Патрубки и шланги охлаждения', 'patrubki'),
                ('Ремни и натяжители',           'remni'),
                ('Водяной насос и ремкомплекты', 'vodyanoy-nasos'),
            ]),
            ('Система смазки', 'smazka', 5, [
                ('Масляный насос и ремкомплекты', 'maslyany-nasos'),
            ]),
            ('Турбокомпрессор', 'turbokompressor', 6, [
                ('ТКР и запчасти', 'tkr'),
            ]),
        ]),
        ('Рулевое управление', 'rulevoe', 'bi-steering', 5, [
            ('ГУР и насосы', 'gur', 1, [
                ('Гидроусилители',    'gidroupraviteli'),
                ('Насосы ГУРа',       'nasosy-gur'),
                ('Ремкомплекты ГУРа', 'remk-gur'),
                ('Гидроцилиндры',     'gidrotsilindry'),
            ]),
            ('Насосы шестерённые НШ', 'nsh', 2, [
                ('НШ', 'nsh-list'),
            ]),
            ('Рулевые тяги', 'rulevye-tyagi', 3, [
                ('Тяги рулевые', 'tyagi-list'),
            ]),
        ]),
        ('Электрооборудование', 'elektro', 'bi-lightning', 6, [
            ('Генераторы', 'generatory', 1, [
                ('Генераторы',            'generatory-list'),
                ('Регуляторы напряжения', 'regulyatory-napryazheniya'),
            ]),
            ('Стартеры', 'startery', 2, [
                ('Стартеры',          'startery-list'),
                ('Бендиксы',          'bendiksy'),
                ('Реле втягивающее',  'rele-vtyagivayushchee'),
                ('Запчасти стартера', 'zapchasti-startera'),
            ]),
            ('Датчики и реле', 'datchiki', 3, [
                ('Датчики',       'datchiki-list'),
                ('Реле',          'rele-list'),
                ('Амперметры',    'ampmetry'),
                ('Выключатели',   'vyklyuchateli'),
                ('Реле поворота', 'rele-povorota'),
            ]),
            ('Оптика', 'optika', 4, [
                ('Лампы',              'lampy'),
                ('Фонари',             'fonari'),
                ('Фары',               'fary'),
                ('Указатели поворота', 'ukazateli-povorota'),
                ('Стёкла фар',         'stekla-far'),
            ]),
            ('Щётки электрических машин', 'shchetki', 5, [
                ('Щётки генератора', 'shchetki-generatora'),
                ('Щётки стартера',   'shchetki-startera'),
            ]),
            ('Электрооборудование прочее', 'elektro-prochee', 6, [
                ('Конвертеры 24/12В',   'konvertery'),
                ('Аккумуляторные узлы', 'akb'),
            ]),
        ]),
        ('Пневмосистема', 'pnevmo', 'bi-wind', 7, [
            ('Шланги и трубки', 'shlangi-pnevmo', 1, [
                ('Шланги пневматические', 'shlangi-list'),
            ]),
            ('Фитинги и хомуты', 'fitingi', 2, [
                ('Фитинги', 'fitingi-list'),
                ('Хомуты',  'khomut'),
            ]),
        ]),
        ('Кузов и кабина', 'kuzov', 'bi-truck', 8, [
            ('Замки и ручки дверей', 'zamki', 1, [
                ('Замки дверей',     'zamki-list'),
                ('Ручки дверей',     'ruchki'),
                ('Стеклоподъёмники', 'steklopodyomniki'),
                ('Тяги управления',  'tyagi-upravleniya'),
            ]),
            ('Облицовка и панели', 'oblitsovka', 2, [
                ('Панели кабины', 'paneli'),
            ]),
        ]),
        ('Запасные части прочие', 'prochee', 'bi-box', 9, [
            ('Прочие детали', 'prochie-detali', 1, [
                ('Прочие детали', 'prochie-list'),
            ]),
        ]),
    ]

    BRANDS = [
        ('КАМАЗ', 'kamaz'), ('МАЗ', 'maz'),   ('Урал', 'ural'),
        ('КрАЗ', 'kraz'),   ('ЗИЛ', 'zil'),   ('ЛиАЗ', 'liaz'),
        ('НЕФАЗ', 'nefaz'), ('Икарус', 'ikarus'), ('ГАЗ', 'gaz'),
        ('МТЗ', 'mtz'),     ('ЯМЗ', 'yamz'),  ('ПАЗ', 'paz'),
    ]

    BRAND_MAP = {
        'КАМАЗ': 'kamaz', 'МАЗ': 'maz',
        'Урал': 'ural',   'УРАЛ': 'ural',
        'КрАЗ': 'kraz',   'КРАЗ': 'kraz',
        'ЗИЛ': 'zil',
        'ЛиАЗ': 'liaz',   'ЛИАЗ': 'liaz',
        'НЕФАЗ': 'nefaz',
        'Икарус': 'ikarus', 'ИКАРУС': 'ikarus',
        'ГАЗ': 'gaz',     'Газель': 'gaz', 'ГАЗЕЛЬ': 'gaz',
        'МТЗ': 'mtz',     'ЯМЗ': 'yamz',  'ПАЗ': 'paz',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cat_lookup: dict = {}
        self._brands: dict = {}
        self._fallback = None
        self._stats = dict(cats=0, brands=0, products=0, misc=0, errors=0)

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== REBUILD CATALOG ==='))
        with transaction.atomic():
            self._step1_categories()
            self._step2_brands()
            self._step3_products()
            self._step4_featured()
        self._step5_stats()

    # ── Шаг 1: категории ─────────────────────────────────────────────────────

    def _step1_categories(self):
        self.stdout.write('Шаг 1: Создание категорий...')
        try:
            from apps.orders.models import OrderItem
            OrderItem.objects.all().delete()
        except Exception:
            pass
        Product.objects.all().delete()
        Category.objects.all().delete()

        for c1_name, c1_slug, c1_icon, c1_ord, subs in self.TREE:
            c1 = Category.objects.create(
                name=c1_name, slug=c1_slug, icon=c1_icon, order=c1_ord
            )
            self._stats['cats'] += 1
            for c2_name, c2_slug, c2_ord, leaves in subs:
                c2 = Category.objects.create(
                    name=c2_name, slug=c2_slug, parent=c1, order=c2_ord
                )
                self._stats['cats'] += 1
                for idx, (c3_name, c3_slug) in enumerate(leaves):
                    c3 = Category.objects.create(
                        name=c3_name, slug=c3_slug, parent=c2, order=idx
                    )
                    self._stats['cats'] += 1
                    self._cat_lookup[(c1_name.lower(), c2_name.lower(), c3_name.lower())] = c3
                    if c3_slug == 'prochie-list':
                        self._fallback = c3

        self.stdout.write(f'  OK Создано: {self._stats["cats"]} категорий')

    # ── Шаг 2: марки ─────────────────────────────────────────────────────────

    def _step2_brands(self):
        self.stdout.write('Шаг 2: Загрузка марок...')
        for name, slug in self.BRANDS:
            b, _ = Brand.objects.update_or_create(
                slug=slug, defaults={'name': name, 'is_active': True}
            )
            self._brands[slug] = b
            self._stats['brands'] += 1
        self.stdout.write(f'  OK Обработано: {self._stats["brands"]} марок')

    # ── Шаг 3: товары ────────────────────────────────────────────────────────

    def _step3_products(self):
        self.stdout.write(f'Шаг 3: Импорт товаров из {self.CSV_PATH}...')
        if not os.path.exists(self.CSV_PATH):
            self.stderr.write(self.style.ERROR(f'  ОШИБКА: файл {self.CSV_PATH} не найден'))
            return

        used_slugs: set = set()

        with open(self.CSV_PATH, encoding='mac_cyrillic', errors='replace') as f:
            reader = csv.reader(f, delimiter=';')
            for row_num, row in enumerate(reader):
                if row_num < 2 or len(row) < 9:
                    continue
                sku = row[0].strip()
                if not sku:
                    continue

                name       = row[1].strip()
                price_raw  = row[2].strip()
                manuf      = row[4].strip() if len(row) > 4 else ''
                brands_raw = row[5].strip() if len(row) > 5 else ''
                c1         = row[6].strip() if len(row) > 6 else ''
                c2         = row[7].strip() if len(row) > 7 else ''
                c3         = row[8].strip() if len(row) > 8 else ''

                if not name or not price_raw:
                    continue

                try:
                    price = Decimal(
                        price_raw.replace('\xa0', '').replace(' ', '').replace(',', '.')
                    )
                except InvalidOperation:
                    self._stats['errors'] += 1
                    continue

                category = self._resolve_cat(c1, c2, c3)
                brands   = self._parse_brands(brands_raw)
                specs    = f'Производитель: {manuf}' if manuf else ''

                base = slugify(sku) or slugify(name[:60]) or f'item-{row_num}'
                slug, n = base, 2
                while slug in used_slugs:
                    slug = f'{base}-{n}'
                    n += 1
                used_slugs.add(slug)

                prod, _ = Product.objects.update_or_create(
                    sku=sku,
                    defaults=dict(
                        name=name, slug=slug, price=price,
                        stock=10, is_active=True,
                        category=category, specifications=specs,
                    ),
                )
                if brands:
                    prod.brands.set(brands)

                self._stats['products'] += 1
                if category == self._fallback:
                    self._stats['misc'] += 1

        self.stdout.write(f'  OK Импортировано: {self._stats["products"]} товаров')

    def _resolve_cat(self, c1: str, c2: str, c3: str):
        key = (c1.lower(), c2.lower(), c3.lower())
        if key in self._cat_lookup:
            return self._cat_lookup[key]
        for (k1, k2, k3), cat in self._cat_lookup.items():
            if k2 == c2.lower() and k3 == c3.lower():
                return cat
        for (k1, k2, k3), cat in self._cat_lookup.items():
            if k3 == c3.lower():
                return cat
        return self._fallback

    def _parse_brands(self, raw: str) -> list:
        if not raw:
            return []
        result = []
        for part in raw.replace(' и ', ', ').split(','):
            part = part.strip()
            slug = self.BRAND_MAP.get(part)
            if slug and slug in self._brands:
                result.append(self._brands[slug])
        return result

    # ── Шаг 4: хиты и новинки ────────────────────────────────────────────────

    def _step4_featured(self):
        self.stdout.write('Шаг 4: Пометка хитов и новинок...')
        best_ids = list(
            Product.objects.filter(is_active=True, category__parent__slug='torm-apparatura')
            .values_list('id', flat=True)[:8]
        )
        Product.objects.filter(id__in=best_ids).update(is_bestseller=True)

        new_ids = list(
            Product.objects.filter(is_active=True, category__parent__slug='valy-kardannye')
            .values_list('id', flat=True)[:8]
        )
        Product.objects.filter(id__in=new_ids).update(is_new=True)
        self.stdout.write(f'  OK Хиты: {len(best_ids)}, Новинки: {len(new_ids)}')

    # ── Шаг 5: статистика ────────────────────────────────────────────────────

    def _step5_stats(self):
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== ИТОГИ ==='))
        lvl1 = Category.objects.filter(parent__isnull=True).count()
        lvl2 = Category.objects.filter(parent__isnull=False, parent__parent__isnull=True).count()
        lvl3 = Category.objects.filter(parent__parent__isnull=False).count()
        self.stdout.write(
            f'Категории: {lvl1} разделов / {lvl2} подразделов / {lvl3} листовых'
        )
        self.stdout.write(f'Марки: {self._stats["brands"]}')
        self.stdout.write(f'Товаров импортировано: {self._stats["products"]}')
        self.stdout.write(f'  в т.ч. «Прочие детали»: {self._stats["misc"]}')
        self.stdout.write(f'Ошибок разбора цены: {self._stats["errors"]}')
        brands_linked = Brand.objects.filter(products__isnull=False).distinct().count()
        self.stdout.write(f'Марок с привязанными товарами: {brands_linked}')
