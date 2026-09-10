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

# Collect static files
RUN python manage.py collectstatic --noinput --settings=blog.settings_prod

# HuggingFace Spaces requires port 7860
EXPOSE 7860

# Run with gunicorn on port 7860
CMD ["gunicorn", "blog.wsgi:application", \
     "--bind", "0.0.0.0:7860", \
     "--workers", "1", \
     "--timeout", "300", \
     "--worker-class", "sync"]
