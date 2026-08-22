# Estágio de build/runtime
FROM python:3.12-slim

# Variáveis de ambiente para Python e Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Adiciona Poetry ao PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Instala dependências de sistema (build-essentials para pacotes que compilam C)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala o Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

# Segurança: Cria usuário não-root (Padrão Fintech/LGPD)
RUN useradd -m -U appuser

# Copia arquivos de dependências primeiro (cache layer)
COPY pyproject.toml poetry.lock* /app/

# Instala dependências (incluindo dev para o MVP)
RUN poetry install --no-root

# Copia o restante do código
COPY . /app/

# Garante permissões ao usuário appuser
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD sh -c "python manage.py migrate && gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000}"