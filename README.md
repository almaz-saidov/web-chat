# web-chat
Реализация веб-чата с двусторонней коммуникацией на основе протокола WebSocket.

## Конфигурация проекта

Для работы проекта необходимо создать файл **.env** в директории **src/core/envs** со следующими переменными окружения:

```
# Сервер
HOST="0.0.0.0"
PORT=8000

# База данных
DB_HOST="postgres"
DB_PORT=5432
DB_USER="postgres"
DB_PASS="postgres"
DB_NAME="web_chat_db"

# JWT токены
PRIVATE_KEY_PATH="core/certs/jwt-private.pem"
PUBLIC_KEY_PATH="core/certs/jwt-public.pem"
ALGORITHM="RS256"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
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
