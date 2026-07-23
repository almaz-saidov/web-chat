# teting_guide.md

## Назначение

Этот проект небольшой: FastAPI API, WebSocket-чат, PostgreSQL, SQLAlchemy, Alembic и статический frontend.
Тесты нужны, чтобы быстро ловить поломки авторизации, токенов, сообщений, миграций и работы с БД.

Тесты запускаются из `src/`:

```bash
poetry run pytest
```

## Структура

```text
src/tests/
├── conftest.py
├── unit_tests/
├── api_tests/
└── integration_tests/
```

## Общие правила

- все тесты асинхронные, если они ходят в API или БД;
- для всех `assert` должны быть написаны сообщения в стиле "что ожидали";
- для HTTP использовать `httpx.AsyncClient` из fixture `async_client`;
- для прямой проверки БД использовать fixture `db_session`;
- для тестовой БД использовать только PostgreSQL из `testcontainers`;
- не подключаться к рабочей БД;
- не хардкодить порт тестовой БД: URL формируется из контейнера;
- таблицы создавать через `alembic upgrade head`, не через `Base.metadata.create_all()`;
- не писать тесты “на всякий случай”. Покрывать только поведение, которое важно для проекта;
- один тест должен проверять один сценарий;
- названия тестов должны описывать условие и ожидаемый результат.

## Unit-тесты

Путь: `src/tests/unit_tests/`.

Unit-тесты проверяют отдельную логику без API и без БД.

Писать unit-тесты для:

- `JWTService`;
- `RefreshTokenService.validate_refresh_token_str`;
- чистых функций и методов без I/O;
- логики подписи после merge ветки с биометрической авторизацией: нормализация, DTW-score, построение шаблона.

Не использовать в unit-тестах:

- `async_client`;
- `db_session`;
- testcontainers;
- реальные файлы проекта, если можно использовать `tmp_path`.

## API-тесты

Путь: `src/tests/api_tests/`.

API-тесты проверяют HTTP-контракт: статус-коды, обязательные поля, формат базового ответа.

Покрывать:

- `GET /api/healthcheck`;
- регистрацию;
- логин;
- refresh/logout;
- protected message endpoints без токена и с токеном;
- `422` на невалидный payload;
- `401` на ошибки авторизации;
- `409` на duplicate username.

Для API-тестов достаточно проверять ответ API. Если важно доказать, что данные реально записались в БД, это уже integration-тест.

Пример:

```python
async def test_register_returns_201_for_valid_payload(async_client):
    response = await async_client.post("/api/auth/register", json={...})

    assert response.status_code == 201
```

## Integration-тесты

Путь: `src/tests/integration_tests/`.

Integration-тесты проверяют цепочку:

```text
route -> service -> repository -> PostgreSQL
```

Писать integration-тест, если сценарий должен подтвердить состояние БД.

Покрывать:

- регистрация создаёт пользователя в `users`;
- пароль хранится как hash;
- login создаёт refresh-token в `refresh_tokens`;
- refresh/logout меняют состояние refresh-токенов;
- создание сообщения сохраняет запись в `messages`;
- получение истории читает данные из БД в ожидаемом порядке;
- каскадное удаление связанных записей, если это важно для задачи;
- после merge подписи: создание `signature_templates` и проверка отказа при неправильной подписи.

Пример:

```python
async def test_create_message_persists_data(async_client, db_session):
    response = await async_client.post("/api/message/create", json={...}, headers={...})

    assert response.status_code == 200

    result = await db_session.execute(...)
    assert result.scalar_one_or_none() is not None
```

## Авторизация в тестах

- не использовать реальные JWT-ключи;
- использовать fixture `jwt_keys`;
- для protected endpoints либо проходить login flow, либо аккуратно генерировать тестовый access token через `JWTService`;
- refresh token проверять через cookie и таблицу `refresh_tokens`.

## Данные и фикстуры

Пока проект маленький, отдельные фабрики не обязательны.

Добавлять фабрики только когда подготовка данных начала повторяться в нескольких тестах. До этого достаточно локальных helper-функций рядом с тестами или fixtures в `conftest.py`.

## Именование

Формат:

```text
test_<action>_<expected_result>_<condition>
```

Примеры:

```python
async def test_login_returns_401_for_wrong_password():
    ...

async def test_create_message_persists_data_for_authorized_user():
    ...
```

## Перед завершением задачи

Если задача добавляет или меняет тесты, проверить:

```bash
cd src
poetry run ruff format .
poetry run ruff check .
poetry run mypy .
poetry run pytest
```

Если тесты требуют Docker, убедиться, что `testcontainers` реально поднял PostgreSQL и миграции дошли до текущего Alembic head.

## Что не делать

- мокать БД в integration-тестах;
- проверять внутреннюю реализацию route-функций через прямой вызов, если нужен API-контракт;
- делать большие end-to-end сценарии, если достаточно unit/API/integration-теста;
- добавлять сложные фабрики, plugins или fixtures;
- тестировать frontend через браузер в рамках backend test suite.
