# Rate Limiter Service

Rate limiter сервис, поддерживающий различные провайдеры с разными конфигурациями лимитов.

## Требования

- Docker
- Docker Compose

## Быстрый старт

1. Клонируйте репозиторий:
```bash
git clone git@github.com:aibekraiymbekov/rate_limiter.git
cd rate-limiter
```

2. Запустите сервис:
```bash
docker-compose up --build
```

Сервис будет доступен по адресу `http://localhost`

## API Endpoints

### Основные endpoints

- `GET /` - Тестовый endpoint
- `GET /rate-limit-status` - Проверка текущего состояния rate limit

### Конфигурация провайдеров

В текущей версии доступны следующие провайдеры:

- `connexpay`: 100 запросов / 30 секунд
- `qolo`: 200 запросов / 60 секунд

## Примеры использования

### Тестовый запрос

```bash
curl -X GET "http://localhost/" \
     -H "Authorization: Bearer your-token" \
     -H "X-Provider: connexpay"
```

### Проверка статуса rate limit

```bash
curl -X GET "http://localhost/rate-limit-status" \
     -H "Authorization: Bearer your-token" \
     -H "X-Provider: connexpay"
```

### Ответ с заголовками rate limit

Каждый ответ содержит заголовки:
- `X-RateLimit-Limit`: максимальное количество запросов
- `X-RateLimit-Remaining`: оставшееся количество запросов
- `X-RateLimit-Reset`: время до сброса в секундах

Пример проверки заголовков:
```bash
curl -i -X GET "http://localhost/" \
     -H "Authorization: Bearer your-token" \
     -H "X-Provider: connexpay"
```

## Ошибки

### 429 Too Many Requests
Возникает при превышении лимита запросов:
```json
{
    "detail": "Too Many Requests for provider connexpay"
}
```

### 400 Bad Request
Возникает при отсутствии или неверном провайдере:
```json
{
    "detail": "Provider is required (use X-Provider header or provider query parameter)"
}
```

### 401 Unauthorized
Возникает при отсутствии или неверном формате токена:
```json
{
    "detail": "Authorization header is missing"
}
```

## Локальная разработка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите сервис:
```bash
uvicorn main:app --reload
```

## Остановка сервиса

Для остановки Docker контейнеров:
```bash
docker-compose down
```

## Структура проекта

```
project/
├── main.py              # FastAPI приложение
├── rate_limiter.py      # Логика rate limiter
├── utils.py             # Вспомогательные функции
├── requirements.txt     # Зависимости Python
├── Dockerfile          
├── docker-compose.yml   
└── nginx/
    └── nginx.conf       # Конфигурация Nginx
```