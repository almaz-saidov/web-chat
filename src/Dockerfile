FROM python:3.12-alpine

RUN apk add --no-cache curl postgresql-dev && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==1.8.2

WORKDIR /usr/web-chat/src

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/usr/web-chat/src/entrypoint.sh"]
