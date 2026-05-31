import os
from django.core.management.base import BaseCommand, CommandError
from apps.integration.views import run_import


class Command(BaseCommand):
    help = 'Импорт товаров из XML CommerceML 2.05'

    def add_arguments(self, parser):
        parser.add_argument('xml_file', type=str, help='Путь к XML-файлу')

    def handle(self, *args, **options):
        path = options['xml_file']
        if not os.path.exists(path):
            raise CommandError(f'Файл не найден: {path}')

        filename = os.path.basename(path)
        self.stdout.write(f'Импорт файла: {filename}')

        with open(path, 'rb') as f:
            log, error = run_import(f, filename)

        if error:
            self.stderr.write(self.style.ERROR(f'❌ Ошибка импорта: {error}'))
            return

        self.stdout.write(self.style.SUCCESS('✅ Импорт завершён успешно!'))
        self.stdout.write(f'📦 Обработано товаров:       {log.count_processed}')
        self.stdout.write(f'🆕 Добавлено новых:           {log.count_created}')
        self.stdout.write(f'🔄 Обновлено цен:             {log.count_price_updated}')
        self.stdout.write(f'📊 Обновлено остатков:        {log.count_stock_updated}')
        self.stdout.write(f'⚠️  Без артикула (→ Прочие):  {log.count_no_sku}')
        self.stdout.write(f'❌ Ошибок:                    {log.count_errors}')
        self.stdout.write(f'🕐 Время импорта: {log.created_at:%H:%M:%S}')
        self.stdout.write(f'📁 Файл: {log.filename}')
