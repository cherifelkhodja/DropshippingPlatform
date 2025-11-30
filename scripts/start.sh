#!/bin/bash
set -e

echo "=== Starting Dropshipping Platform ==="

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h ${DB_HOST:-postgres} -p ${DB_PORT:-5432} -U ${POSTGRES_USER:-dropshipping} -q 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "Database is ready!"

# If arguments are passed (e.g., celery command), execute them directly
if [ $# -gt 0 ]; then
    echo "Starting with custom command: $@"
    exec "$@"
fi

# Default behavior: run migrations and start uvicorn
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete!"

# Start the application
echo "Starting uvicorn server..."
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8000
