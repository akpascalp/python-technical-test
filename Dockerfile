FROM python:alpine3.18 AS build

WORKDIR /app

RUN pip install poetry==2.1.2

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-root && \
    rm -rf /root/.cache/

RUN adduser --disabled-password appuser && \
    chown -R appuser:appuser /app

ENV PYTHONPATH="/app"

USER appuser
