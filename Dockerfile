FROM python:3.11-slim

# System configuration level utilities allocation parameters
RUN apt-get update && apt-get install -y \
    libpq-dev gcc netcat-traditional && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Extracting Python Dependencies Matrix
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instantiating Core System Directories for Data Persistence Logs
RUN mkdir -p /app/logs /app/media /app/staticfiles

COPY . .

# Granting Absolute Execution Overrides for Live File Uploads Safety
RUN chmod -R 755 /app/media /app/logs

EXPOSE 8000