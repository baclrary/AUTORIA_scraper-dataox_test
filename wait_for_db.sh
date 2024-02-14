#!/bin/sh

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h $DB_HOST -U $DB_USER -d $DB_NAME; do
  sleep 2
done
echo "PostgreSQL is ready."

PGPASSWORD=$DB_PASS psql -v ON_ERROR_STOP=1 --host="$DB_HOST" --username "$DB_USER" --dbname "$DB_NAME" <<-EOSQL
CREATE TABLE IF NOT EXISTS cars (
    id SERIAL PRIMARY KEY,
    url VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255),
    price_usd INTEGER,
    odometer INTEGER,
    username VARCHAR(255),
    phone_number VARCHAR(20),
    image_url VARCHAR(255),
    images_count INTEGER,
    car_number VARCHAR(20),
    car_vin VARCHAR(20),
    datetime_found TIMESTAMP
);
EOSQL
