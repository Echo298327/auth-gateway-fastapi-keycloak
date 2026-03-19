FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY iam/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY iam/src/ .
COPY shared/ ./shared/

RUN useradd -m appuser
USER appuser

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8081/readyz || exit 1

CMD ["python", "main.py"]
