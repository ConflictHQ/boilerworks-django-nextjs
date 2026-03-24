FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    git \
    gcc \
    build-essential \
    cron \
    postgresql-client \
    ca-certificates \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip pipenv wheel

WORKDIR /boilerworks

COPY Pipfile Pipfile.lock ./
RUN pipenv requirements --dev > requirements.txt && pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=config.settings

CMD ["python", "startup.py"]
