FROM python:3.11-slim AS build

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock /app/

RUN poetry export -f requirements.txt --output requirements.txt

RUN apt-get update && apt-get install -y wget

RUN wget https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_amd64.tar.gz

RUN tar -xzf CloudflareST_linux_amd64.tar.gz

FROM python:3.11-slim

WORKDIR /app

COPY --from=build /app/requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY *.py /app

COPY --from=build /app/CloudflareST /app/CloudflareST

RUN chmod +x /app/CloudflareST

ENV CDN_ST_DNS_CST_PATH=/app/CloudflareST

CMD ["python", "main.py"]