import base64
import json
import re
from datetime import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from apps.catalog.models import Category, Product
from apps.integration.models import Exchange1CLog, ProductBackup
from apps.integration.parser import parse_xml


# ──────────────────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────────────────

def _transliterate(text):
    mapping = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo',
        'ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m',
        'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
        'ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
        'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    }
    result = ''
    for ch in text.lower():
        result += mapping.get(ch, ch)
    return result


def _make_slug(name):
    return slugify(_transliterate(name))[:80]


def _get_or_create_category(category_name):
    if not category_name:
        return _get_misc_category()
    try:
        return Category.objects.get(name=category_name)
    except Category.DoesNotExist:
        pass
    slug = _make_slug(category_name)
    base_slug = slug
    counter = 1
    while Category.objects.filter(slug=slug).exists():
        slug = f'{base_slug}-{counter}'
        counter += 1
    return Category.objects.create(name=category_name, slug=slug, is_active=True)


def _get_misc_category():
    cat, _ = Category.objects.get_or_create(
        slug='prochie-list',
        defaults={'name': 'Прочие детали', 'is_active': True},
    )
    return cat


def _next_no_art_sku():
    existing = (
        Product.objects
        .filter(sku__startswith='NO-ART-')
        .values_list('sku', flat=True)
    )
    max_num = 0
    for sku in existing:
        m = re.match(r'NO-ART-(\d+)$', sku)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f'NO-ART-{max_num + 1:04d}'


def _make_product_slug(name, sku):
    base = _make_slug(f'{name} {sku}')
    slug = base
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


# ──────────────────────────────────────────────────────────
# Предпросмотр (dry run) — БД не меняется
# ──────────────────────────────────────────────────────────

def preview_import(parsed):
    """
    Анализирует распарсенные товары и возвращает список изменений
    без записи в БД.
    Каждый элемент: {action, sku, name, price_old, price_new,
                     stock_old, stock_new, category_name}
    """
    changes = []
    stats = {'created': 0, 'price_updated': 0, 'stock_updated': 0,
             'no_sku': 0, 'unchanged': 0, 'errors': 0}

    for item in parsed['products']:
        sku = (item['sku'] or '').strip()
        name = item['name']
        price_new = item['price']
        stock_new = item['stock']
        stock_present = item.get('stock_present', False)
        category_name = item.get('category_name') or 'Прочие детали'

        try:
            if sku:
                try:
                    product = Product.objects.get(sku=sku)
                    changed_price = product.price != price_new
                    changed_stock = stock_present and product.stock != stock_new

                    if changed_price or changed_stock:
                        action = []
                        if changed_price:
                            action.append('price')
                            stats['price_updated'] += 1
                        if changed_stock:
                            action.append('stock')
                            stats['stock_updated'] += 1
                        changes.append({
                            'action': 'update',
                            'action_label': _action_label(changed_price, changed_stock),
                            'sku': sku,
                            'name': product.name,
                            'price_old': product.price,
                            'price_new': price_new,
                            'stock_old': product.stock,
                            'stock_new': stock_new if stock_present else product.stock,
                            'category_name': product.category.name,
                            'changed_price': changed_price,
                            'changed_stock': changed_stock,
                        })
                    else:
                        stats['unchanged'] += 1
                        changes.append({
                            'action': 'unchanged',
                            'action_label': 'Без изменений',
                            'sku': sku,
                            'name': product.name,
                            'price_old': product.price,
                            'price_new': price_new,
                            'stock_old': product.stock,
                            'stock_new': stock_new if stock_present else product.stock,
                            'category_name': product.category.name,
                            'changed_price': False,
                            'changed_stock': False,
                        })

                except Product.DoesNotExist:
                    stats['created'] += 1
                    changes.append({
                        'action': 'create',
                        'action_label': 'Новый товар',
                        'sku': sku,
                        'name': name,
                        'price_old': None,
                        'price_new': price_new,
                        'stock_old': None,
                        'stock_new': stock_new,
                        'category_name': category_name,
                        'changed_price': True,
                        'changed_stock': True,
                    })
            else:
                stats['no_sku'] += 1
                try:
                    product = Product.objects.get(name=name)
                    changes.append({
                        'action': 'update_no_sku',
                        'action_label': 'Без артикула (обновление)',
                        'sku': product.sku,
                        'name': name,
                        'price_old': product.price,
                        'price_new': price_new,
                        'stock_old': product.stock,
                        'stock_new': stock_new,
                        'category_name': product.category.name,
                        'changed_price': product.price != price_new,
                        'changed_stock': product.stock != stock_new,
                    })
                except Product.DoesNotExist:
                    stats['created'] += 1
                    changes.append({
                        'action': 'create_no_sku',
                        'action_label': 'Без артикула (новый)',
                        'sku': 'NO-ART-????',
                        'name': name,
                        'price_old': None,
                        'price_new': price_new,
                        'stock_old': None,
                        'stock_new': stock_new,
                        'category_name': 'Прочие детали',
                        'changed_price': True,
                        'changed_stock': True,
                    })
                except Product.MultipleObjectsReturned:
                    stats['no_sku'] += 1

        except Exception as e:
            stats['errors'] += 1
            changes.append({
                'action': 'error',
                'action_label': 'Ошибка',
                'sku': sku or '—',
                'name': name,
                'price_old': None,
                'price_new': price_new,
                'stock_old': None,
                'stock_new': stock_new,
                'category_name': '—',
                'error': str(e),
                'changed_price': False,
                'changed_stock': False,
            })

    return changes, stats


def _action_label(changed_price, changed_stock):
    parts = []
    if changed_price:
        parts.append('цена')
    if changed_stock:
        parts.append('остаток')
    return 'Обновление: ' + ', '.join(parts)


# ──────────────────────────────────────────────────────────
# Ядро импорта (реальная запись в БД)
# ──────────────────────────────────────────────────────────

def run_import(file_obj, filename):
    try:
        parsed = parse_xml(file_obj)
    except ValueError as e:
        log = Exchange1CLog.objects.create(
            filename=filename,
            status=Exchange1CLog.STATUS_ERROR,
            error_text=str(e),
        )
        return log, str(e)

    log = Exchange1CLog.objects.create(
        filename=filename,
        status=Exchange1CLog.STATUS_ERROR,
    )

    stats = {
        'processed': 0,
        'created': 0,
        'price_updated': 0,
        'stock_updated': 0,
        'no_sku': 0,
        'errors': 0,
        'details': [],
        'stock_in_xml': 0,
    }

    try:
        with transaction.atomic():
            for item in parsed['products']:
                try:
                    _process_item(item, log, stats)
                    stats['processed'] += 1
                except Exception as e:
                    stats['errors'] += 1
                    stats['details'].append({
                        'sku': item.get('sku') or '—',
                        'name': item.get('name', ''),
                        'error': str(e),
                    })

            log.status = Exchange1CLog.STATUS_SUCCESS
            log.count_processed = stats['processed']
            log.count_created = stats['created']
            log.count_price_updated = stats['price_updated']
            log.count_stock_updated = stats['stock_updated']
            log.count_no_sku = stats['no_sku']
            log.count_errors = stats['errors']
            details_data = {'items': stats['details']}
            if stats['stock_in_xml'] == 0:
                details_data['no_stock_warning'] = True
            log.details = json.dumps(details_data, ensure_ascii=False)
            log.save()

    except Exception as e:
        log.status = Exchange1CLog.STATUS_ERROR
        log.error_text = str(e)
        log.save()
        return log, str(e)

    return log, None


def _process_item(item, log, stats):
    sku = (item['sku'] or '').strip()
    name = item['name']
    price = item['price']
    stock = item['stock']
    stock_present = item.get('stock_present', False)

    if stock_present:
        stats['stock_in_xml'] += 1

    if sku:
        try:
            product = Product.objects.get(sku=sku)
            _backup(product, log, 'updated')
            changed_price = product.price != price
            changed_stock = stock_present and product.stock != stock
            update_fields = ['price', 'updated_at']
            product.price = price
            if stock_present:
                product.stock = stock
                update_fields.append('stock')
            product.save(update_fields=update_fields)
            if changed_price:
                stats['price_updated'] += 1
            if changed_stock:
                stats['stock_updated'] += 1
        except Product.DoesNotExist:
            category = _get_or_create_category(item.get('category_name'))
            slug = _make_product_slug(name, sku)
            product = Product.objects.create(
                sku=sku, name=name, slug=slug,
                price=price, stock=stock if stock_present else 0,
                category=category, is_active=True,
            )
            _backup(product, log, 'created')
            stats['created'] += 1
    else:
        stats['no_sku'] += 1
        misc_cat = _get_misc_category()
        try:
            product = Product.objects.get(name=name)
            _backup(product, log, 'updated')
            update_fields = ['price', 'updated_at']
            product.price = price
            if stock_present:
                product.stock = stock
                update_fields.append('stock')
            product.save(update_fields=update_fields)
        except Product.DoesNotExist:
            auto_sku = _next_no_art_sku()
            slug = _make_product_slug(name, auto_sku)
            product = Product.objects.create(
                sku=auto_sku, name=name, slug=slug,
                price=price, stock=stock if stock_present else 0,
                category=misc_cat, no_sku=True, is_active=True,
            )
            _backup(product, log, 'created')
            stats['created'] += 1
        except Product.MultipleObjectsReturned:
            product = Product.objects.filter(name=name).first()
            _backup(product, log, 'updated')
            update_fields = ['price', 'updated_at']
            product.price = price
            if stock_present:
                product.stock = stock
                update_fields.append('stock')
            product.save(update_fields=update_fields)


def _backup(product, log, action):
    ProductBackup.objects.create(
        log=log,
        product_id=product.pk,
        sku=product.sku,
        name=product.name,
        price=product.price,
        stock=product.stock,
        is_active=product.is_active,
        action=action,
    )


# ──────────────────────────────────────────────────────────
# Views
# ──────────────────────────────────────────────────────────

@staff_member_required
def import_view(request):
    if request.method == 'POST':
        xml_file = request.FILES.get('xml_file')
        if not xml_file:
            messages.error(request, 'Файл не выбран.')
            return redirect('integration:import')

        # Читаем файл и сохраняем в сессии для последующего применения
        raw = xml_file.read()
        filename = xml_file.name

        try:
            import io
            parsed = parse_xml(io.BytesIO(raw))
        except ValueError as e:
            messages.error(request, f'Ошибка парсинга XML: {e}')
            return redirect('integration:import')

        # Предпросмотр изменений
        changes, stats = preview_import(parsed)

        # Сохраняем сырой XML в сессии (base64) для применения
        request.session['pending_xml'] = base64.b64encode(raw).decode('ascii')
        request.session['pending_filename'] = filename

        return render(request, 'integration/import_preview.html', {
            'changes': changes,
            'stats': stats,
            'filename': filename,
            'total': len(changes),
        })

    # GET — страница загрузки
    last_log = Exchange1CLog.objects.filter(
        status=Exchange1CLog.STATUS_SUCCESS
    ).first()
    return render(request, 'integration/import.html', {'last_log': last_log})


@staff_member_required
@require_POST
def import_confirm_view(request):
    """Применяет импорт из XML сохранённого в сессии."""
    raw_b64 = request.session.get('pending_xml')
    filename = request.session.get('pending_filename', 'unknown.xml')

    if not raw_b64:
        messages.error(request, 'Данные предпросмотра устарели. Загрузите файл заново.')
        return redirect('integration:import')

    import io
    raw = base64.b64decode(raw_b64)
    log, error = run_import(io.BytesIO(raw), filename)

    # Очищаем сессию
    request.session.pop('pending_xml', None)
    request.session.pop('pending_filename', None)

    return redirect('integration:import_result', pk=log.pk)


@staff_member_required
def import_result_view(request, pk):
    log = get_object_or_404(Exchange1CLog, pk=pk)
    return render(request, 'integration/import_result.html', {'log': log})


@staff_member_required
@require_POST
def rollback_last_view(request):
    log = Exchange1CLog.objects.filter(
        status=Exchange1CLog.STATUS_SUCCESS
    ).first()

    if not log:
        messages.error(request, 'Нет импортов для отката.')
        return redirect('integration:import')

    with transaction.atomic():
        for backup in log.backups.all():
            if backup.action == 'created':
                Product.objects.filter(pk=backup.product_id).delete()
            elif backup.action == 'updated':
                Product.objects.filter(pk=backup.product_id).update(
                    price=backup.price,
                    stock=backup.stock,
                )
        log.status = Exchange1CLog.STATUS_ROLLED_BACK
        log.save(update_fields=['status'])

    messages.success(request, f'Импорт «{log.filename}» откатан.')
    return redirect('integration:import')


@staff_member_required
def export_catalog_view(request):
    from apps.integration.export import generate_catalog_xml
    xml_bytes = generate_catalog_xml()
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(xml_bytes, content_type='application/xml; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="kameks_export_{now}.xml"'
    return response
