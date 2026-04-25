FROM redis:7-alpine

# Экспорт порта Redis
EXPOSE 6379

# Запуск Redis в режиме сохранения данных (опционально)
CMD ["redis-server", "--appendonly", "yes"]
