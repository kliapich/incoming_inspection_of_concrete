# Настройка Railway PostgreSQL для проекта Beton_control

## 🚀 Что такое Railway?

Railway - это платформа для развертывания приложений и баз данных в облаке. Она предоставляет простой способ создания и управления PostgreSQL базами данных.

## 📋 Предварительные требования

1. Учетная запись на [Railway.app](https://railway.app)
2. Python 3.8+
3. Git (опционально)

## 🔧 Пошаговая настройка

### Шаг 1: Создание базы данных на Railway

1. Зайдите на [Railway.app](https://railway.app) и войдите в свой аккаунт
2. Нажмите "New Project"
3. Выберите "Provision PostgreSQL"
4. Дождитесь создания базы данных
5. Нажмите на созданную базу данных

### Шаг 2: Получение параметров подключения

В разделе "Connect" вы увидите:

- **Host**: `your-project.railway.app`
- **Port**: `5432` (обычно)
- **Database**: `railway`
- **Username**: `postgres`
- **Password**: `your-password`

### Шаг 3: Настройка переменных окружения

1. Скопируйте файл `config.env.example` в `.env`:
   ```bash
   cp config.env.example .env
   ```

2. Отредактируйте файл `.env`:
   ```env
   # Railway Database Configuration
   RAILWAY_DB_HOST=your-project.railway.app
   RAILWAY_DB_PORT=5432
   RAILWAY_DB_NAME=railway
   RAILWAY_DB_USER=postgres
   RAILWAY_DB_PASSWORD=your-password
   
   # Или используйте DATABASE_URL (скопируйте из Railway)
   DATABASE_URL=postgresql://postgres:password@host:port/railway
   
   # Telegram Bot Token
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   
   # Режим работы с базой данных
   DB_TYPE=postgresql
   
   # Fallback к SQLite если PostgreSQL недоступен
   USE_SQLITE_FALLBACK=true
   ```

### Шаг 4: Установка зависимостей

```bash
pip install -r requirements.txt
```

### Шаг 5: Миграция данных

Если у вас уже есть данные в SQLite, выполните миграцию:

```bash
python migrate_to_railway.py
```

### Шаг 6: Тестирование подключения

```bash
python -c "
from database_manager import DatabaseManager
db = DatabaseManager()
print('Тип БД:', db.db_type)
print('Информация о подключении:', db.get_connection_info())
print('Тест соединения:', db.test_connection())
db.close()
"
```

## 🔄 Использование в приложении

### Автоматическое переключение

Приложение автоматически:
1. Попытается подключиться к PostgreSQL Railway
2. Если не получится - переключится на SQLite
3. Покажет информацию о текущем типе базы данных

### Ручное переключение

В файле `.env` измените:
```env
DB_TYPE=sqlite  # Для SQLite
DB_TYPE=postgresql  # Для PostgreSQL
```

## 📊 Мониторинг и управление

### Railway Dashboard

В Railway Dashboard вы можете:
- Видеть статистику использования
- Мониторить производительность
- Управлять резервными копиями
- Настраивать масштабирование

### Логи приложения

Приложение ведет логи подключения к базе данных:
- Успешные подключения
- Ошибки подключения
- Переключения между типами БД

## 🚨 Устранение неполадок

### Ошибка подключения к PostgreSQL

1. Проверьте правильность параметров в `.env`
2. Убедитесь, что база данных активна в Railway
3. Проверьте firewall и настройки сети
4. Попробуйте использовать `DATABASE_URL` вместо отдельных параметров

### Ошибка миграции

1. Убедитесь, что SQLite файл существует
2. Проверьте права доступа к файлам
3. Проверьте логи миграции

### Fallback к SQLite

Если PostgreSQL недоступен, приложение автоматически переключится на SQLite. Это можно отключить:

```env
USE_SQLITE_FALLBACK=false
```

## 💡 Рекомендации

### Безопасность

1. Никогда не коммитьте файл `.env` в Git
2. Используйте сильные пароли
3. Регулярно обновляйте пароли

### Производительность

1. Используйте connection pooling для PostgreSQL
2. Оптимизируйте запросы
3. Мониторьте использование ресурсов

### Резервное копирование

1. Настройте автоматические бэкапы в Railway
2. Регулярно экспортируйте данные
3. Тестируйте восстановление из бэкапа

## 🔗 Полезные ссылки

- [Railway Documentation](https://docs.railway.app/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

## 📞 Поддержка

Если у вас возникли проблемы:

1. Проверьте логи приложения
2. Проверьте статус Railway
3. Создайте issue в репозитории проекта
4. Обратитесь в поддержку Railway

---

**Удачи с настройкой Railway! 🎉**
