import asyncio
import json

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


async def get_total_pages(base_url: str) -> int:
    """
    Determines the total number of pages in the car search results.

    Args:
        base_url (str): The base URL for the car search.

    Returns:
        int: The total number of pages of search results.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(f"{base_url}&size=100")
        await page.wait_for_selector("span#staticResultsCount")

        page_content = await page.content()
        soup = BeautifulSoup(page_content, "html.parser")

        items = soup.select("#searchPagination .page-item.mhide a.page-link")
        total_pages = 1  # Default to 1 in case of no pagination found
        if items:
            page_numbers = [int(item.get("data-page", "0")) for item in items]
            total_pages = max(page_numbers, default=1)

        await browser.close()
        return total_pages


# extra
async def save_to_json(data: dict, filename: str = "data.json") -> None:
    """
    Saves scraped data to a JSON file, avoiding duplicates.

    Args:
        data (dict): The data to save.
        filename (str): The filename of the JSON file.
    """
    try:
        with open(filename, "r+", encoding="utf-8") as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    if not any(item["url"] == data["url"] for item in existing_data):
        existing_data.append(data)
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4, ensure_ascii=False)


async def fetch_with_retry(client, url, retries=3, delay=1):
    """
    Attempts to fetch a URL with retries.

    Args:
        client: The httpx.AsyncClient instance.
        url (str): The URL to fetch.
        retries (int): Maximum number of retries.
        delay (int): Delay between retries in seconds.

    Returns:
        An httpx.Response object on success.

    Raises:
        httpx.HTTPError: When the maximum number of retries is exceeded.
    """
    for attempt in range(retries):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response
        except (httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException) as e:
            if attempt == retries - 1:
                return None
            await asyncio.sleep(delay)
