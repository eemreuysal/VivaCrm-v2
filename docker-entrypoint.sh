#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

postgres_ready() {
python << END
import sys
import psycopg2
try:
    psycopg2.connect(
        dbname="${POSTGRES_DB}",
        user="${POSTGRES_USER}",
        password="${POSTGRES_PASSWORD}",
        host="${POSTGRES_HOST}",
        port="${POSTGRES_PORT}",
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

redis_ready() {
python << END
import sys
import redis
try:
    rs = redis.Redis.from_url("${REDIS_URL}")
    rs.ping()
except redis.exceptions.ConnectionError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done
>&2 echo 'PostgreSQL is available'

until redis_ready; do
  >&2 echo 'Waiting for Redis to become available...'
  sleep 1
done
>&2 echo 'Redis is available'

# Apply database migrations
>&2 echo 'Applying database migrations...'
python manage.py migrate

# Create cache tables
>&2 echo 'Creating cache tables...'
python manage.py createcachetable

# Create log directory
mkdir -p logs

# Execute the command passed to docker-entrypoint.sh
exec "$@"