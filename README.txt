# VAGVIN - VIN проверка автомобилей

![CI/CD Status](https://github.com/igorkoshensky/vagvin/actions/workflows/main.yml/badge.svg)

Django веб-приложение для комплексной проверки VIN номеров автомобилей с интеграцией множественных сервисов проверки, системой платежей и мониторингом.

## 🚀 Особенности

- **Множественная проверка VIN**: Autoteka, Carfax, VIN History, аукционы
- **Система платежей**: Robokassa, YooKassa, Heleket
- **Пользовательские аккаунты**: регистрация, авторизация, личный кабинет
- **Система отзывов**: модерация отзывов пользователей
- **CI/CD**: автоматизированное тестирование и развертывание
- **Мониторинг**: Prometheus + Grafana с кастомными метриками
- **Docker**: контейнеризация всех сервисов

## 📋 Требования

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (для продакшена)
- Git

## 🛠 Установка и запуск

### Быстрый старт с Docker

```bash
# Клонировать репозиторий
git clone https://github.com/igorkoshensky/vagvin.git
cd vagvin

# Создать .env файл
cp .env.example .env
# Отредактировать .env под ваши настройки

# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps
```

Приложение будет доступно по адресу: http://localhost:9999

### Локальная разработка

```bash
# Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или .venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить базу данных
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Запустить сервер разработки
python manage.py runserver
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Тесты с покрытием
pytest --cov=apps --cov-report=html

# Тесты конкретного приложения
pytest apps/accounts/tests.py

# Линтинг
flake8

# Форматирование кода
black .
```

### Генерация тестовых данных

```bash
# Создание тестовых платежей
python manage.py generate_test_payments 100

# Создание тестовых отзывов
python manage.py generate_test_reviews 50

# Для Docker
docker-compose exec web python manage.py generate_test_payments 100
docker-compose exec web python manage.py generate_test_reviews 50
```

### CI/CD

Проект включает GitHub Actions workflow с тремя этапами:

1. **Lint & Test** - проверка кода и запуск тестов
2. **Build Docker** - сборка Docker образов
3. **Mock Deploy** - имитация развертывания

## 📊 Мониторинг

### Доступ к интерфейсам

- **Grafana Dashboard**: http://localhost:3000
  - Логин: `admin` / Пароль: `admin`
- **Prometheus**: http://localhost:9090
- **Django Metrics**: http://localhost:9999/metrics/

### Дашборды

1. **VAGVIN Django Application Dashboard** - кастомный дашборд с:
   - Метрики пользователей (общее количество, активные за 24ч)
   - HTTP статистика (запросы по методам, время ответа)
   - Бизнес-метрики (VIN запросы, платежи)
   - Производительность приложения

2. **Django Dashboard** - стандартный дашборд Django метрик

### Кастомные метрики

```bash
# Обновить метрики вручную
curl http://localhost:9999/update-metrics/

# Просмотр метрик
curl http://localhost:9999/metrics/ | grep django
```

Автоматически собираются метрики:
- Регистрации и логины пользователей
- Количество объектов в БД по моделям
- Успешные/неудачные платежи
- Сгенерированные отчеты и отзывы
- HTTP запросы и время ответа

## 🏗 Архитектура

### Структура проекта

```
vagvin/
├── apps/                    # Django приложения
│   ├── accounts/           # Пользователи и аутентификация
│   ├── pages/              # Статические страницы
│   ├── payments/           # Система платежей
│   ├── reports/            # VIN отчеты и проверки
│   └── reviews/            # Отзывы пользователей
├── vagvin/                 # Основные настройки Django
├── static/                 # Статические файлы
├── templates/              # HTML шаблоны
├── grafana/                # Конфигурация Grafana
├── prometheus/             # Конфигурация Prometheus
└── docker-compose.yml      # Docker сервисы
```

### Сервисы Docker

- **web** - Django приложение
- **db** - PostgreSQL база данных  
- **prometheus** - сбор метрик
- **grafana** - визуализация метрик

## 🔧 Конфигурация

### Переменные окружения (.env)

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,web

# Database
DATABASE_URL=postgresql://user:password@db:5432/vagvin

# API Keys (опционально)
CARSTAT_API_KEY=your-api-key
VINHISTORY_LOGIN=your-login
VINHISTORY_PASS=your-password

# Payment Systems (опционально)
ROBOKASSA_LOGIN=your-login
ROBOKASSA_PASSWORD1=your-password1
ROBOKASSA_PASSWORD2=your-password2
YOOKASSA_SHOP_ID=your-shop-id
YOOKASSA_SECRET_KEY=your-secret
```

### Настройка продакшена

1. Обновите `ALLOWED_HOSTS` в настройках
2. Настройте HTTPS
3. Используйте внешнюю PostgreSQL БД
4. Настройте резервное копирование
5. Добавьте Nginx для статических файлов

## 🔌 API

### VIN проверка

```bash
# Autoteka проверка
POST /reports/autoteka/
Content-Type: application/json
{"vin": "WBAFR12040LM12345"}

# Carfax проверка  
POST /reports/carfax/
Content-Type: application/json
{"vin": "WBAFR12040LM12345"}

# VIN History проверка
POST /reports/vinhistory/
Content-Type: application/json
{"vin": "WBAFR12040LM12345"}

# Аукционы
POST /reports/auction/
Content-Type: application/json
{"vin": "WBAFR12040LM12345"}
```

### Платежи

```bash
# Создание платежа
POST /payments/robokassa/
Content-Type: application/json
{"amount": 100, "total_amount": 110}

# Статус платежа
GET /payments/status/{payment_id}/
```

### Метрики

```bash
# Все метрики Prometheus
GET /metrics/

# Обновление кастомных метрик
GET /update-metrics/
```

## 🚦 Статус сервисов

### Проверка работоспособности

```bash
# Статус всех контейнеров
docker-compose ps

# Логи сервисов
docker logs vagvin-web-1
docker logs prometheus  
docker logs grafana

# Проверка подключений
curl http://localhost:9999/        # Django app
curl http://localhost:9090/        # Prometheus
curl http://localhost:3000/        # Grafana
```

### Troubleshooting

**Проблема**: Containers не запускаются
```bash
# Проверить логи
docker-compose logs

# Пересобрать образы
docker-compose build --no-cache
docker-compose up -d
```

**Проблема**: Метрики не отображаются в Grafana
```bash
# Проверить targets в Prometheus
open http://localhost:9090/targets

# Обновить метрики
curl http://localhost:9999/update-metrics/

# Перезапустить Grafana
docker-compose restart grafana
```

**Проблема**: База данных недоступна
```bash
# Проверить подключение к БД
docker-compose exec db psql -U postgres -d vagvin

# Применить миграции
docker-compose exec web python manage.py migrate
```

## 🤝 Разработка

### Workflow

1. Создать ветку: `git checkout -b feature/new-feature`
2. Внести изменения
3. Запустить тесты: `pytest`
4. Зафиксировать: `git commit -m "Add new feature"`
5. Отправить: `git push origin feature/new-feature`
6. Создать Pull Request

### Добавление новых метрик

1. В `vagvin/monitoring.py` добавить метрику:
```python
new_metric = Counter('django_new_metric_total', 'Description')
```

2. В нужном месте вызвать:
```python
from vagvin.monitoring import new_metric
new_metric.inc()
```

3. Обновить дашборд в Grafana

## 📄 Лицензия

MIT License - подробности в файле LICENSE

## 📞 Поддержка

- Issues: https://github.com/chupakobra6/vagvin/issues
- Email: igorpheik@gmail.com
- Telegram: @Pheik15