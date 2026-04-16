# GitHub Guardian Backend
Run `docker-compose up -d redis` to start Redis.
Run `celery -A src.core.celery_app worker --loglevel=info` to start Celery.
Run `uvicorn src.main:app --reload --port 8000` to start FastAPI.
