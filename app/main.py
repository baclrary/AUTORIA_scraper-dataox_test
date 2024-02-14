import asyncio
import os
import time

import schedule
from database import dump_db
from scraper import CarScraper


async def run_scraper(base_url: str) -> None:
    """
    Runs the car scraper for the given base URL.

    Args:
        base_url (str): The base URL to start scraping from.
    """
    start = time.time()
    scraper = CarScraper()
    await scraper.start(base_url)
    end = time.time()
    print("Data collected. Spent time: ", end - start)


def schedule_tasks() -> None:
    """Schedules tasks for running the scraper and database dump based on environment variables."""
    dump_time = os.getenv("DUMP_TIME")
    start_time = os.getenv("START_TIME")

    schedule.every().day.at(start_time).do(
        lambda: asyncio.create_task(
            run_scraper(
                # Link to ALL used cars ↓↓↓
                # "https://auto.ria.com/uk/search/?indexName=auto&country.import.usa.not=-1&price.currency=1&abroad.not=-1&custom.not=-1"
                # Link to SMALLER amount of used cars ↓↓↓
                "https://auto.ria.com/uk/search/?indexName=auto&year[0].gte=2022&categories.main.id=1&brand.id[0]=48&country.import.usa.not=-1&price.currency=1&abroad.not=-1&custom.not=-1"
            )
        )
    )
    schedule.every().day.at(dump_time).do(lambda: asyncio.create_task(dump_db()))


async def run_scheduled_tasks() -> None:
    """Continuously runs scheduled tasks."""
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def main():
    """Main function to schedule and run tasks."""
    schedule_tasks()
    await run_scheduled_tasks()


if __name__ == "__main__":
    asyncio.run(main())
