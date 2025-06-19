#!/bin/bash

set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
python << END
import sys
import time
import psycopg2
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

for attempt in range(30):
    try:
        logger.info(f"Attempt {attempt+1}/30: Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            dbname="vagvin",
            user="postgres",
            password="postgres",
            host="db",
            port="5432"
        )
        conn.close()
        logger.info("Successfully connected to PostgreSQL!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        logger.info(f"PostgreSQL is not ready yet: {e}")
        time.sleep(1)

logger.error("Failed to connect to PostgreSQL after 30 attempts")
sys.exit(1)
END

# Create necessary directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p media
mkdir -p staticfiles

# Apply migrations
echo "Applying database migrations..."
python manage.py migrate contenttypes
python manage.py migrate auth
python manage.py migrate accounts
python manage.py migrate admin
python manage.py migrate sessions
python manage.py migrate payments
python manage.py migrate reports
python manage.py migrate reviews
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting application..."
exec "$@" 