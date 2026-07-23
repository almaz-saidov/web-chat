FROM python:3.14-alpine

RUN apk add --no-cache curl

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==2.4.1

WORKDIR /usr/web-chat/src

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-cache

COPY . .
