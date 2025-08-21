FROM python:3.9-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директорию для базы данных
RUN mkdir -p /app/data

# Копируем базу данных (если есть)
COPY concrete.db /app/data/concrete.db

# Устанавливаем права на базу данных
RUN chmod 644 /app/data/concrete.db

# Открываем порт
EXPOSE 8000

# Переменные окружения по умолчанию
ENV RAILWAY_DB_PATH=/app/data/concrete.db
ENV DB_TYPE=sqlite

# Запускаем приложение
CMD ["python", "Beton_control_v2.0.py"]
