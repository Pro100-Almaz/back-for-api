FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app *before* entrypoint; your compose bind-mount may shadow /app
COPY . .

# Copy entrypoint to a path that won't be shadowed by a bind mount
COPY entrypoint.sh /usr/local/bin/app-entrypoint.sh

# Ensure LF endings and +x
RUN sed -i 's/\r$//' /usr/local/bin/app-entrypoint.sh \
 && chmod +x /usr/local/bin/app-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/app-entrypoint.sh"]
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
