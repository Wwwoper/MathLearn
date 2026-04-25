FROM ollama/ollama:latest

# Экспорт порта Ollama API
EXPOSE 11434

# Директория для хранения моделей
VOLUME /root/.ollama

# Запуск Ollama serve
CMD ["ollama", "serve"]
