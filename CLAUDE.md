# КАМЭКС — Веб-портал запчастей

**Дипломный проект (ВКР)** студента 5 курса БГТУ «ВОЕНМЕХ», группа О722Б, Настин А.А.

## Стек

- Python 3.12, Django 5.0, PostgreSQL 16
- Bootstrap 5 + Bootstrap Icons (CDN)
- Docker Compose + nginx (продакшн)
- gunicorn (WSGI-сервер)

## Архитектура

```
kameks/
├── apps/
│   ├── main/       # Главная, О компании, Доставка, Контакты
│   ├── catalog/    # Каталог, карточка товара, поиск, фильтры
│   ├── cart/       # Корзина (session-based)
│   ├── orders/     # Оформление и история заказов
│   └── accounts/   # Регистрация, вход, личный кабинет
├── kameks/         # Конфиг-пакет Django
│   └── settings/
│       ├── base.py
│       ├── development.py   # DJANGO_SETTINGS_MODULE по умолчанию
│       └── production.py
├── templates/      # Все HTML-шаблоны
├── static/         # CSS, JS, изображения
│   ├── css/variables.css
│   ├── css/main.css
│   └── js/main.js
├── media/          # Загружаемые пользователями файлы
└── staticfiles/    # collectstatic output (только в проде)
```

## Запуск (разработка)

```bash
# Активировать venv
venv\Scripts\activate

# Запустить сервер (SQLite для разработки без PG)
python manage.py runserver
```

`DJANGO_SETTINGS_MODULE=kameks.settings.development`

## Запуск (Docker)

```bash
docker compose up --build
```

Сервис доступен на http://localhost (nginx → gunicorn → Django + PostgreSQL).

## Переменные окружения (.env)

```
SECRET_KEY=...
DB_NAME=kameks_db
DB_USER=kameks_user
DB_PASSWORD=kameks_password
DB_HOST=db          # в Docker — имя сервиса
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Управление

```bash
# Создать суперпользователя
python manage.py createsuperuser

# Загрузить тестовые данные
python manage.py loaddata fixtures/initial_data.json

# Собрать статику (только для прода)
python manage.py collectstatic
```

## Дизайн

Тёмный промышленный B2B стиль. Цветовая схема через CSS-переменные в `static/css/variables.css`:
- `--color-bg-primary: #0d1b2a` — основной фон
- `--color-accent-blue: #2e86de` — акцент
- `--color-accent-orange: #e67e22` — акцент (КАМАЗ)
- `--color-accent-red: #c0392b` — акцент (КАМАЗ)

## Ключевые решения

- Корзина — session-based (без БД-модели)
- Избранное — sessionStorage JS (визуальное, без бэкенда)
- AJAX-добавление в корзину через fetch() + CSRF
- `UserProfile` как OneToOne к стандартному User
- Фильтры каталога через `django-filter` + Q-поиск
