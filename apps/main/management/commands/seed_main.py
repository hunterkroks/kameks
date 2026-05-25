from django.core.management.base import BaseCommand
from apps.main.models import Advantage, Review


ADVANTAGES = [
    {
        'icon': 'bi-shield-check',
        'title': 'Гарантия качества',
        'description': '12 месяцев на все запчасти. На оригинальные детали — гарантия производителя.',
        'order': 1,
    },
    {
        'icon': 'bi-truck',
        'title': 'Доставка по России',
        'description': 'Отправляем транспортными компаниями СДЭК, ПЭК, Деловые линии. От 1 рабочего дня.',
        'order': 2,
    },
    {
        'icon': 'bi-box-seam',
        'title': 'Большой склад',
        'description': 'Более 15 000 позиций в наличии. Большинство заказов отгружаем в день обращения.',
        'order': 3,
    },
    {
        'icon': 'bi-headset',
        'title': 'Техподдержка',
        'description': 'Квалифицированные менеджеры помогут подобрать запчасть по VIN, артикулу или фото.',
        'order': 4,
    },
    {
        'icon': 'bi-currency-exchange',
        'title': 'Честные цены',
        'description': 'Прямые поставки от производителей. Без скрытых наценок. Оптовые цены для юрлиц.',
        'order': 5,
    },
    {
        'icon': 'bi-award',
        'title': '20 лет на рынке',
        'description': 'Работаем с 2004 года. Более 5000 постоянных клиентов по всей России и СНГ.',
        'order': 6,
    },
]

REVIEWS = [
    {
        'author_name': 'Александр Петров',
        'author_company': 'ООО «ТрансСервис»',
        'text': 'Заказываем запчасти для нашего парка КАМАЗов уже третий год. Качество отличное, доставка быстрая. Особенно порадовала оперативность менеджеров — помогли подобрать нестандартную деталь буквально за час.',
        'rating': 5,
    },
    {
        'author_name': 'Игорь Сидоров',
        'author_company': 'ИП Сидоров И.В.',
        'text': 'Брал турбокомпрессор для КАМАЗа-65115. Аналог BOSCH, цена разумная, уже 8 месяцев работает без нареканий. Доставка до Екатеринбурга заняла 3 дня.',
        'rating': 5,
    },
    {
        'author_name': 'Светлана Морозова',
        'author_company': 'АТП г. Казань',
        'text': 'Обслуживаем 40 единиц техники. КАМЭКС — один из немногих поставщиков, у кого всегда есть запчасти на МАЗы. Работаем по безналу, выставляют счета оперативно.',
        'rating': 4,
    },
    {
        'author_name': 'Дмитрий Козлов',
        'author_company': 'Строительная компания «Урал-Строй»',
        'text': 'Покупаем запчасти для Урал-4320. Продавцы разбираются в технике — это важно, потому что на старых машинах артикулы иногда отличаются. Нашли нужную деталь, когда другие разводили руками.',
        'rating': 5,
    },
    {
        'author_name': 'Руслан Ахметов',
        'author_company': 'ПАО «ДорСтрой»',
        'text': 'Удобный сайт, можно найти запчасть по OEM-номеру. Заказываем регулярно, ни разу не подвели. Единственное пожелание — добавить больше фото к товарам.',
        'rating': 4,
    },
]


class Command(BaseCommand):
    help = 'Заполняет раздел main: преимущества и отзывы'

    def handle(self, *args, **options):
        self.stdout.write('Создание преимуществ...')
        for data in ADVANTAGES:
            adv, created = Advantage.objects.update_or_create(
                title=data['title'],
                defaults=data,
            )
            if created:
                self.stdout.write(f'  + {adv.title}')

        self.stdout.write('Создание отзывов...')
        for data in REVIEWS:
            rev, created = Review.objects.get_or_create(
                author_name=data['author_name'],
                author_company=data.get('author_company', ''),
                defaults=data,
            )
            if created:
                self.stdout.write(f'  + {rev.author_name}')

        self.stdout.write(self.style.SUCCESS('\nГотово! Преимущества и отзывы добавлены.'))
