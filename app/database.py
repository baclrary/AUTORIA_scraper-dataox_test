import os
import subprocess
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

load_dotenv(verbose=True, override=True)


db_config = {
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASS"),
    "database": os.environ.get("DB_NAME"),
    "host": os.environ.get("DB_HOST"),
}


async def create_db_pool(db_config: dict) -> asyncpg.Pool:
    """Creates a connection pool to the database.

    Args:
        db_config (dict): Database configuration.

    Returns:
        asyncpg.Pool: The connection pool.
    """
    return await asyncpg.create_pool(**db_config)


async def dump_db() -> None:
    """Dumps the database content to a SQL file."""
    os.makedirs("dumps", exist_ok=True)
    current_time = datetime.now()
    filename = f"{db_config['database']}_backup_{current_time.strftime('%d%m%Y_%H%M%S')}.sql"
    file_path = os.path.join("dumps", filename)

    command = f"pg_dump -h {db_config['host']} -U {db_config['user']} -d {db_config['database']} -f {file_path}"
    try:
        subprocess.run(command, shell=True, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during database dump: {e}")


async def save_car_to_db(car_details: dict, pool: asyncpg.Pool) -> None:
    """Saves car details to the database.

    Args:
        car_details (dict): The car details to save.
        pool (asyncpg.Pool): The database connection pool.
    """
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO cars(url, title, price_usd, odometer, username, phone_number, image_url, images_count, car_number, car_vin, datetime_found)
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (url) DO NOTHING
            """,
            car_details["url"],
            car_details["title"],
            car_details["price_usd"],
            car_details["odometer"],
            car_details["username"],
            car_details["phone_number"],
            car_details["image_url"],
            car_details["images_count"],
            car_details["car_number"],
            car_details["car_vin"],
            car_details["datetime_found"],
        )
