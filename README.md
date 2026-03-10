# web-chat
Реализация веб-чата с двусторонней коммуникацией на основе протокола WebSocket.

## Конфигурация проекта

Для работы проекта необходимо создать файл **.env.${ENVIRONMENT}** в директории **src/core/envs** со следующими переменными окружения:

```
# Окружение
ENVIRONMENT=

# Сервер
SERVER_HOST=
SERVER_PORT=

# База данных
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

# JWT токены
PRIVATE_KEY_PATH=
PUBLIC_KEY_PATH=
ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=
REFRESH_TOKEN_EXPIRE_DAYS=
```

## Генерация RSA ключей для JWT

Для работы аутентификации необходимо создать пару RSA ключей по указанным в .env.${ENVIRONMENT} путям:

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
│       └── .env.${ENVIRONMENT}
├── ... (остальные файлы проекта)
```

# Запустить проект
```
docker compose --env-file ./src/core/envs/.env.${ENVIRONMENT} up --build -d
```

# Остановить проект
```
docker compose --env-file ./src/core/envs/.env.${ENVIRONMENT} down
```
