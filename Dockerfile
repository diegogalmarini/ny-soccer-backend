FROM python:3.8-slim-bullseye
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc pkg-config libmariadb-dev libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
RUN pip install "pip<24.0"
RUN pip install --no-cache-dir --pre -r /app/requirements.txt
RUN pip install --no-cache-dir gunicorn==20.1.0 pymysql
COPY . /app
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD gunicorn nycs.wsgi:application --bind 0.0.0.0:$PORT
