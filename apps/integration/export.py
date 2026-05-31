"""Генерация XML CommerceML 2.05 из БД."""
import xml.etree.ElementTree as ET
from xml.dom import minidom

from apps.catalog.models import Category, Product


def generate_catalog_xml():
    root = ET.Element('КоммерческаяИнформация', attrib={'ВерсияСхемы': '2.05'})
    catalog_el = ET.SubElement(root, 'Каталог')

    # Классификатор с категориями
    classifier = ET.SubElement(catalog_el, 'Классификатор')
    groups_el = ET.SubElement(classifier, 'Группы')
    for cat in Category.objects.filter(is_active=True).order_by('order', 'name'):
        g = ET.SubElement(groups_el, 'Группа')
        ET.SubElement(g, 'Ид').text = str(cat.pk)
        ET.SubElement(g, 'Наименование').text = cat.name

    # Товары
    products_el = ET.SubElement(catalog_el, 'Товары')
    for product in Product.objects.filter(is_active=True).select_related('category'):
        t = ET.SubElement(products_el, 'Товар')
        ET.SubElement(t, 'Ид').text = str(product.pk)
        ET.SubElement(t, 'Артикул').text = product.sku
        ET.SubElement(t, 'Наименование').text = product.name

        groups_ref = ET.SubElement(t, 'Группы')
        ET.SubElement(groups_ref, 'Ид').text = str(product.category_id)

        ET.SubElement(t, 'БазоваяЕдиница').text = 'шт'

        prices_el = ET.SubElement(t, 'Цены')
        price_el = ET.SubElement(prices_el, 'Цена')
        ET.SubElement(price_el, 'ЦенаЗаЕдиницу').text = str(product.price)
        ET.SubElement(price_el, 'Валюта').text = 'RUB'

        stocks_el = ET.SubElement(t, 'Остатки')
        stock_el = ET.SubElement(stocks_el, 'Остаток')
        ET.SubElement(stock_el, 'Количество').text = str(product.stock)

    raw = ET.tostring(root, encoding='unicode')
    pretty = minidom.parseString(raw).toprettyxml(indent='  ', encoding='utf-8')
    return pretty
