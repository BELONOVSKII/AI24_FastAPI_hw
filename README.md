# FastAPI Сокращатель URL с Аутентификацией

RESTful API, построенное с использованием FastAPI, которое позволяет пользователям:

- Регистрироваться и аутентифицироваться с помощью JWT
- Сокращать URL с возможностью указания пользовательских псевдонимов и срока действия
- Искать, обновлять, удалять и получать статистику по ссылкам
- Управлять учетными записями пользователей, включая поддержку операций администратора
- Использует Redis для кеширования и SQLAlchemy для операций с базой данных

---

## Функции API

### Аутентификация

- `POST /auth/register` – Регистрация нового пользователя
- `POST /auth/jwt/login` – Получение JWT токена доступа
- `POST /auth/jwt/logout` – Выход и отзыв токена

### Управление ссылками

- `POST /links/shorten` – Создание короткой ссылки
- `GET /links/{short_code}` – Перенаправление на оригинальный URL
- `GET /links/{short_code}/stats` – Получение статистики использования
- `PUT /links/{short_code}` – Обновление короткой ссылки
- `DELETE /links/{short_code}` – Удаление ссылки
- `GET /links/search` – Поиск ссылок по оригинальному URL

### Управление пользователями

- `GET /users/me` – Получение информации о текущем пользователе
- `PATCH /users/me` – Обновление информации о текущем пользователе
- `GET /users/{id}` – Получение информации о любом пользователе (только для администратора)
- `PATCH /users/{id}` – Обновление информации о пользователе (только для администратора)
- `DELETE /users/{id}` – Удаление пользователя (только для администратора)

---

## Примеры запросов

### Регистрация пользователя

**Запрос**
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Ответ**
```json
{
  "id": "c05dbbcb-b3ff-44ff-8df7-4a6f13544b83",
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false
}
```

---

### Вход в систему

**Запрос**
```http
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

**Ответ**
```json
{
  "access_token": "your.jwt.token.here",
  "token_type": "bearer"
}
```

---

### Сокращение URL

**Запрос**
```http
POST /links/shorten?original_url=https://example.com&custom_alias=my-link&expires_at=2025-12-31T23:59:00
Authorization: Bearer <access_token>
```

**Ответ**
```json
{
  "short_code": "my-link",
  "original_url": "https://example.com",
  "expires_at": "2025-12-31T23:59:00"
}
```

---

### Получить статистику по ссылке

**Запрос**
```http
GET /links/my-link/stats
```

**Ответ**
```json
{
  "short_code": "my-link",
  "original_url": "https://example.com",
  "clicks": 42,
  "created_at": "2024-01-01T12:00:00",
  "expires_at": "2025-12-31T23:59:00"
}
```

---

## Требования

- Python 3.10+
- Docker и Docker Compose

## Запуск локально

Клонируйте репозиторий и выполните:

```bash
docker-compose up --build
```

FastAPI будет доступен по адресу:

- Документация API: `http://localhost:8000/docs`
- OpenAPI схема: `http://localhost:8000/openapi.json`

---

## Конфигурация окружения

Скопируйте в `.env` и настройте:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fastapi_db
REDIS_URL=redis://redis:6379
SECRET=your-secret
```

---

## База данных

Приложение использует SQLAlchemy и базу данных PostgreSQL.

## Redis

Redis используется для кеширования популярных ссылок и кеширования статистик по популярным ссылкам.

--- 
## Background tasks
Фоновые задачи реализованы с помощью `fastapi.BackgroundTasks` и используются для удаления ссылок с истекшим сроком хранения.  

---
## Пример деплоя и использования сервиса
![Example](assets/720.gif)