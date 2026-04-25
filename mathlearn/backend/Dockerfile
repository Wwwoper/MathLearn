FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy pyproject.toml and install dependencies
COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run migrations and then start the application
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
