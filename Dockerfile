FROM python:3.10

WORKDIR /app

RUN apt-get update && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install playwright && \
    playwright install chromium && \
    playwright install-deps

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app
COPY wait_for_db.sh ./

RUN chmod +x wait_for_db.sh

EXPOSE 80
