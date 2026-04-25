FROM postgres:16-alpine

# Переменные окружения по умолчанию
ENV POSTGRES_USER=mathlearn
ENV POSTGRES_PASSWORD=mathlearn_password
ENV POSTGRES_DB=mathlearn_db

# Копирование скриптов инициализации (если будут)
COPY ./init-scripts /docker-entrypoint-initdb.d/

# Экспорт порта PostgreSQL
EXPOSE 5432
