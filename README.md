# web-chat
Реализация веб-чата с двусторонней коммуникацией на основе протокола WebSocket.

## Конфигурация проекта

Для работы проекта необходимо создать файл **.env** в директории **src/core/envs** со следующими переменными окружения:

```
# Сервер
HOST=
PORT=

# База данных
DB_HOST=
DB_PORT=
DB_USER=
DB_PASS=
DB_NAME=

# JWT токены
PRIVATE_KEY_PATH=
PUBLIC_KEY_PATH=
ALGORITHM=
ACCESS_TOKEN_EXPIRE_MINUTES=
REFRESH_TOKEN_EXPIRE_DAYS=
```

## Генерация RSA ключей для JWT

Для работы аутентификации необходимо создать пару RSA ключей по указанным в .env путям.

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
