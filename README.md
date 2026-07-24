# web-chat
Реализация веб-чата с двусторонней коммуникацией на основе протокола WebSocket.

## Конфигурация проекта

Для работы проекта необходимо создать файл **.env** в директории **src/core/envs** со следующими переменными окружения:

```
# === СЕТЕВЫЕ ПАРАМЕТРЫ СЕРВЕРА ПРИЛОЖЕНИЯ ===
SERVER_HOST=
SERVER_PORT=

# === ПАРАМЕТРЫ ПОДКЛЮЧЕНИЯ К ХРАНИЛИЩУ ДАННЫХ ===
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

# === КОНФИГУРАЦИЯ КРИПТОГРАФИЧЕСКОЙ СИСТЕМЫ JWT ===
PRIVATE_KEY_PATH=
PUBLIC_KEY_PATH=
ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=
REFRESH_TOKEN_EXPIRE_DAYS=

# === ПАРАМЕТРЫ БИОМЕТРИЧЕСКОЙ ВЕРИФИКАЦИИ ПОДПИСИ ===
SIGNATURE_MIN_POINT_COUNT=5
SIGNATURE_SAMPLE_COUNT=5
SIGNATURE_NORMALIZED_POINT_COUNT=1024

SIGNATURE_MAX_DURATION_PENALTY_RATIO=2.0
SIGNATURE_TIME_WEIGHT=0.15

SIGNATURE_BREAK_COUNT_WEIGHT=0.3
SIGNATURE_PRESSURE_WEIGHT=0.35
SIGNATURE_TILT_WEIGHT=0.35

SIGNATURE_COORDINATE_WEIGHT=1.0
SIGNATURE_DURATION_WEIGHT=0.4

SIGNATURE_MATCH_THRESHOLD=0.85
```

## Генерация RSA ключей для JWT

Для работы аутентификации необходимо создать пару RSA ключей по указанным в **.env** путям:

```
# Генерация приватного ключа
openssl genrsa -out src/core/certs/jwt-private.pem 2048

# Извлечение публичного ключа из приватного
openssl rsa -in src/core/certs/jwt-private.pem -pubout -out src/core/certs/jwt-public.pem
```

## Структура после генерации

После выполнения всех шагов структура проекта должна выглядеть так:

```
src/
├── core/
│   └── certs/
│       ├── jwt-private.pem
│       └── jwt-public.pem
│   └── envs/
│       └── .env
├── ... (остальные файлы проекта)
```

# Запустить проект
```
docker compose --env-file ./src/core/envs/.env up --build -d
```

# Остановить проект
```
docker compose --env-file ./src/core/envs/.env down
```
