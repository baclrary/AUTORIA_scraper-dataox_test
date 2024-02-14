import asyncio
import json
import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from database import create_db_pool, db_config, save_car_to_db
from tqdm.asyncio import tqdm  # beautiful progess bar
from utils import fetch_with_retry, get_total_pages


class CarScraper:
    def __init__(self, sem: int = 30) -> None:
        """
        Initializes the CarScraper.

        Args:
            sem (int): The maximum number of concurrent requests.
        """
        self._sem = asyncio.Semaphore(sem)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=60.0),
            limits=httpx.Limits(max_connections=30, max_keepalive_connections=30),
        )

    async def start(self, base_url: str) -> None:
        """
        Starts the scraping process from the given base URL.

        Args:
            base_url (str): The base URL to start scraping from.
        """
        async with self._client:
            self.pool = await create_db_pool(db_config)

            total_pages = await get_total_pages(base_url)
            car_links = await self._collect_car_links(base_url, total_pages)

            progress_bar = tqdm(
                total=len(car_links),
                desc="Scraping car details",
                colour="#ffff00",
                unit="car",
                bar_format="{l_bar}{bar}| {unit} {n_fmt}/{total_fmt}",
            )

            tasks = [self._scrape_car_details_with_semaphore(link, progress_bar) for link in car_links]
            car_details_list = await asyncio.gather(*tasks)
            save_tasks = [
                save_car_to_db(car_details, self.pool) for car_details in car_details_list if car_details is not None
            ]
            await asyncio.gather(*save_tasks)

    async def _collect_car_links(self, base_url: str, total_pages: int) -> list[str]:
        """
        Collects car listing links from all pages of the search results.

        Args:
            base_url (str): The base URL for the car search.
            total_pages (int): The total number of pages to scrape.

        Returns:
            list[str]: A list of car listing URLs.
        """

        async def fetch_links_from_page(page: int) -> list[str]:
            async with self._sem:  # Control concurrency with the semaphore
                response = await fetch_with_retry(self._client, f"{base_url}&page={page}&size=100", 5)
                soup = BeautifulSoup(response.text, "html.parser")
                return [link["href"] for link in soup.select("div#searchResults section.ticket-item .address[href]")]

        progress_bar = tqdm(
            total=total_pages,
            desc="Collecting cars from pages",
            colour="#00e1ff",
            unit="page",
            bar_format="{l_bar}{bar}| {unit} {n_fmt}/{total_fmt}",
        )

        tasks = [fetch_links_from_page(page) for page in range(1, total_pages + 1)]
        car_links = []

        for task in asyncio.as_completed(tasks):
            page_links = await task
            car_links.extend(page_links)
            progress_bar.update(1)

        progress_bar.close()
        return car_links

    async def _scrape_car_details(self, url: str) -> dict:
        """
        Scrapes car details from a given car listing URL.

        Args:
            url (str): The URL of the car listing to scrape.

        Returns:
            dict: A dictionary containing scraped car details.
        """
        try:
            response = await fetch_with_retry(self._client, url, 5)
            self.soup = BeautifulSoup(response.text, "html.parser")
        except Exception:  # for cases when car was deleted
            return {}

        return {
            "url": url,
            "title": self._get_title(),
            "price_usd": self._get_price_usd(),
            "odometer": self._get_odometer(),
            "username": self._get_username(),
            "phone_number": await self._get_phone_number(),
            "image_url": self._get_image_url(),
            "images_count": self._get_images_count(),
            "car_number": self._get_car_number(),
            "car_vin": self._get_car_vin(),
            "datetime_found": datetime.now(),
        }

    def _get_title(self) -> str | None:
        """
        Extracts the title of the car from the page.

        Returns:
            str | None: The title of the car if found, otherwise None.
        """
        title_tag = self.soup.find("h1", class_="head")
        return title_tag.text.strip() if title_tag else None

    def _get_price_usd(self) -> int:
        """
        Extracts the price in USD of the car from the page.

        Returns:
            int: The price of the car in USD, or 0 if not found.
        """
        price_value = self.soup.find("div", class_="price_value")
        return int(re.sub(r"\D", "", price_value.strong.text)) if price_value else 0

    def _get_odometer(self) -> int:
        """
        Extracts the odometer reading of the car from the page.

        Returns:
            int: The odometer reading in kilometers, or 0 if not found.
        """
        odometer_div = self.soup.find("div", class_="base-information")
        if odometer_div:
            span_element = odometer_div.find("span")
            if span_element:
                odometer_text = span_element.text
                return int(re.sub(r"\D", "", odometer_text)) * 1000
        return 0

    def _get_username(self) -> str | None:
        """
        Extracts the username of the seller from the page.

        Returns:
            str | None: The username of the seller if found, otherwise None.
        """
        seller_info = self.soup.find(class_="seller_info_name")
        return seller_info.text.strip() if seller_info else None

    def _get_image_url(self) -> str | None:
        """
        Extracts the main image URL of the car from the page.

        Returns:
            str | None: The URL of the main car image if found, otherwise None.
        """
        image_div = self.soup.find("div", class_="photo-620x465")
        if image_div and image_div.find("picture"):
            img_tag = image_div.find("picture").find("img")
            if img_tag and "src" in img_tag.attrs:
                return img_tag["src"]
        return None

    def _get_images_count(self) -> int:
        """
        Counts the number of images available for the car on the page.

        Returns:
            int: The number of images found for the car.
        """
        photo_container = self.soup.find("div", attrs={"photocontainer": "photo"})
        return len(photo_container.find_all("a")) if photo_container else 0

    def _get_car_number(self) -> str | None:
        """
        Extracts the car's registration number from the page.

        Returns:
            str | None: The car's registration number if found, otherwise None.
        """
        state_num_span = self.soup.find("span", class_="state-num")
        return "".join(re.findall(r"[A-Z0-9]+", state_num_span.text)) if state_num_span else None

    def _get_car_vin(self) -> str | None:
        """
        Extracts the car's VIN (Vehicle Identification Number) from the page.

        Returns:
            str | None: The car's VIN if found, otherwise None.
        """
        car_vin_span = self.soup.find("span", class_="label-vin") or self.soup.find("span", class_="vin-code")
        return car_vin_span.text.strip() if car_vin_span else None

    async def _get_phone_number(self) -> str | None:
        """
        Asynchronously extracts the seller's phone number from the page.

        Returns:
            str | None: The seller's phone number if found, otherwise None.
        """
        script_tag = self.soup.find("script", class_=re.compile("js-user-secure-\d+"))
        phone_id = self.soup.body.get("data-auto-id", "")
        hash = script_tag.get("data-hash", "") if script_tag else ""
        expires = script_tag.get("data-expires", "") if script_tag else ""

        api_url = f"https://auto.ria.com/users/phones/{phone_id}/"
        response = await self._client.get(api_url, params={"hash": hash, "expires": expires})

        try:
            phone_response_json = response.json()
        except json.JSONDecodeError:
            # Attempt to get phone was blocked
            return None

        phone_response_json = response.json()
        phone_number = "+380" + re.sub(r"\D", "", phone_response_json.get("formattedPhoneNumber", ""))[-9:]
        return phone_number

    async def _scrape_car_details_with_semaphore(self, link: str, progress_bar: tqdm) -> dict:
        """
        Asynchronously scrapes car details using a semaphore to limit concurrency.

        Args:
            link (str): The URL of the car listing to scrape.
            progress_bar (tqdm): The tqdm progress bar instance to update.

        Returns:
            dict: A dictionary containing the scraped car details.
        """
        async with self._sem:
            car_details = await self._scrape_car_details(link)
            progress_bar.update(1)
        return car_details
