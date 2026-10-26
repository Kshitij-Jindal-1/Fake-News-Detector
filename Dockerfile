FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Use production settings
ENV DJANGO_SETTINGS_MODULE=blog.settings_prod

# Collect static files
RUN python manage.py collectstatic --noinput

# HuggingFace Spaces expects port 7860
EXPOSE 7860

# Use gunicorn for production
CMD ["gunicorn", "blog.wsgi:application", "--bind", "0.0.0.0:7860", "--timeout", "300", "--workers", "1", "--threads", "4"]
