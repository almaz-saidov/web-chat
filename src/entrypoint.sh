#!/bin/sh
echo "Running database migrations..."
alembic upgrade head
exec python main.py