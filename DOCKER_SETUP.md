# Docker Setup Guide

## Quick Start

1. **Set up environment variables:**
   ```bash
   # Copy and edit the environment file
   cp .env.example .env
   # Edit .env with your actual values
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build
   ```

3. **Access your application:**
   - Django: http://localhost:8001
   - PostgreSQL: localhost:5433
   - Redis: localhost:6380

## Services

- **web**: Django app on port 8001 (to avoid FastAPI conflict)
- **db**: PostgreSQL on port 5433 (to avoid local PostgreSQL conflict)
- **redis**: Redis cache on port 6380
- **celery**: Background worker (optional)
- **celery-beat**: Scheduler (optional)

## Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f web

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access database
docker-compose exec db psql -U django_user -d django_db
```

## Data Persistence

All data is saved in Docker volumes:
- postgres_data: Database files
- redis_data: Cache data
- static_volume: Static files
- media_volume: Media files
