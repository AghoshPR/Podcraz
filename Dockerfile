# Use a minimal Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for MySQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    netcat-traditional \
    nginx \ 
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

COPY .env .env

# Collect static files
RUN python manage.py collectstatic --noinput


RUN mkdir -p /app/media /app/staticfiles \
    && chmod -R 755 /app/media /app/staticfiles

# Expose Django's default port
EXPOSE 8000

# Copy the wait-for-db script
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /wait-for-db.sh
ENTRYPOINT ["/wait-for-db.sh"]

