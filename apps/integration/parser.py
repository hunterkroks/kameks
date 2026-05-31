"""
Парсер XML CommerceML 2.05 для импорта товаров из 1С.
Поддерживает файлы с категориями (<Классификатор>) и без.
"""
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation


NS = '{urn:1C.ru:commerceml_2}'  # пространство имён CommerceML 2.05


def _tag(name):
    """Возвращает тег с пространством имён и без — для поиска."""
    return [f'{NS}{name}', name]


def _find(element, *path_parts):
    """Ищет дочерний элемент по тегу, пробуя оба варианта (с NS и без)."""
    current = element
    for part in path_parts:
        found = None
        for tag in _tag(part):
            found = current.find(tag)
            if found is not None:
                break
        if found is None:
            return None
        current = found
    return current


def _findall(element, tag):
    result = []
    for t in _tag(tag):
        result = element.findall(t)
        if result:
            break
    return result


def _text(element, *path_parts, default=''):
    el = _find(element, *path_parts)
    if el is not None and el.text:
        return el.text.strip()
    return default


def parse_price(raw):
    """'1 750,00' → Decimal('1750.00')"""
    if not raw:
        return Decimal('0')
    cleaned = raw.strip().replace('\xa0', '').replace(' ', '').replace(',', '.')
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal('0')


def parse_xml(file_obj):
    """
    Парсит XML CommerceML 2.05.
    Возвращает dict:
      {
        'categories': {id: {'name': ..., 'parent_id': ...}},
        'products': [{'sku', 'name', 'price', 'stock', 'category_id', 'category_name'}, ...]
      }
    """
    try:
        tree = ET.parse(file_obj)
    except ET.ParseError as e:
        raise ValueError(f'Некорректный XML: {e}')

    root = tree.getroot()

    # Ищем блок Каталог (может быть прямым дочерним или через КоммерческаяИнформация)
    catalog = _find(root, 'Каталог') or root

    # Парсим категории из Классификатор/Группы
    categories = {}
    classifier = _find(catalog, 'Классификатор')
    if classifier is not None:
        _parse_groups(_find(classifier, 'Группы'), categories, parent_id=None)

    # Парсим товары
    products = []
    товары = _find(catalog, 'Товары')
    if товары is None:
        raise ValueError('В XML не найден блок <Товары>')

    for товар in _findall(товары, 'Товар'):
        item = _parse_product(товар, categories)
        if item is not None:
            products.append(item)

    return {'categories': categories, 'products': products}


def _parse_groups(groups_el, result, parent_id):
    if groups_el is None:
        return
    for group in _findall(groups_el, 'Группа'):
        gid = _text(group, 'Ид')
        gname = _text(group, 'Наименование')
        if gid:
            result[gid] = {'name': gname, 'parent_id': parent_id}
        # Вложенные группы
        nested = _find(group, 'Группы')
        if nested is not None:
            _parse_groups(nested, result, parent_id=gid)


def _parse_product(товар, categories):
    sku = _text(товар, 'Артикул').strip()
    name = _text(товар, 'Наименование').strip()

    if not name:
        return None

    price_raw = _text(товар, 'Цены', 'Цена', 'ЦенаЗаЕдиницу')
    price = parse_price(price_raw)

    stock_raw = _text(товар, 'Остатки', 'Остаток', 'Количество')
    try:
        stock = int(Decimal(stock_raw.replace(',', '.').replace(' ', ''))) if stock_raw else 0
    except (InvalidOperation, ValueError):
        stock = 0

    # Категория товара
    category_id = None
    category_name = None
    группы_el = _find(товар, 'Группы')
    if группы_el is not None:
        ids = _findall(группы_el, 'Ид')
        if ids:
            category_id = ids[0].text.strip() if ids[0].text else None
            if category_id and category_id in categories:
                category_name = categories[category_id]['name']

    return {
        'sku': sku,
        'name': name,
        'price': price,
        'stock': stock,
        'category_id': category_id,
        'category_name': category_name,
    }
