
# DataOx: Homework - AutoRia parser

## Introduction

This is a test task I had to complete for DataOx in 24h. The project was tested and works fine on both macOS and Linux.

## Table of Contents

- [Project Structure](#project-structure)
- [Installation](#installation)

## Project Structure:
```
├── Dockerfile                     # Defines the Docker container environment.
├── README.md                      # Project documentation including setup and usage instructions.
├── app                            # Main application directory.
│   ├── database.py                # Handles database connections and operations.
│   ├── main.py                    # Main script; handles scheduling.
│   ├── scraper.py                 # Contains logic for web scraping and data extraction.
│   └── utils.py                   # Utility functions.
├── docker-compose.yaml            # Configuration for Docker Compose to simplify Docker deployment.
├── dumps                          # Directory for database dump files.
│   ├── car_data_backup_14022024_094834.sql  # Example DB dump file.
│   └── car_data_backup_14022024_094936.sql  # Another example DB dump file.
├── requirements.txt               # Lists dependencies for easy installation via pip.
└── wait_for_db.sh                 # Shell script to wait for the database to be ready before proceeding.

Code Explanations:

main.py:
- Uses asyncio for asynchronous programming, enabling non-blocking operations.
- Utilizes the schedule library to run scraping and database dumping tasks at configured times.
- Integrates functionality from other modules (database.py for DB operations, scraper.py for scraping).

scraper.py:
- Implements an asynchronous web scraper using httpx and BeautifulSoup for HTTP requests and HTML parsing.
- Manages concurrency with asyncio.Semaphore to control the rate of simultaneous requests.
- Fetches car listing pages, extracts details, and uses utility functions to interact with the database.

database.py:
- Establishes a connection pool to the PostgreSQL database using asyncpg for efficient database access.
- Provides a function for dumping the database contents to a file, facilitating backups.
- Contains a function to save scraped car details to the database, handling data insertion.

utils.py:
- Includes a function to calculate the total number of pages to scrape by analyzing pagination elements.
- Provides an additional utility to save scraped data to a JSON file, offering an alternative data storage method.

wait_for_db.sh:
- A utility script to ensure the PostgreSQL database is available before attempting to create tables or start the application.
```

## Installation

There are two methods to install the project:
## 1. Using Docker
Advantages:\
\+ Easy and straightforward

Disadvantages: \
\- Slower

### 1.1. Copy the example environment file as .env and provide your values:
Unix:
```
cp .env.example .env
```
Windows:
```
copy .env.example .env
```
### 1.2 Build and run with Docker Compose:
```
docker compose build && docker compose run app
```

## 2. Using CIL:

Advantages:\
\+ Faster

Disadvantages: \
\- Requires setup

### 2.1. Create and activate virtual environment:
Create virtualenv
   ```
   virtualenv venv -p3.10
   ```
Activate (Unix):
```
source venv/bin/activate
```
Activate (Windows):
```
.\venv\activate
```
### 2.2. Install dependencies:
Project dependencies
```
pip install -r requirements.txt
```
For DB dump functionality:
```
sudo apt-get install postgresql-client
```

### 3. Create DB and table in PostgreSQL:
   ```
   CREATE DATABASE cars;
   ```
   ```
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
    datetime_found TIMESTAMP);
   ```

### 4. Copy the example environment file and setup:
```
cp .env.example .env
```

### 5. Run project:
```
python app/main.py
```
