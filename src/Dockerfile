FROM python:3.12-alpine

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==1.8.2

WORKDIR /usr/web-chat/src

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-cache

COPY . .
