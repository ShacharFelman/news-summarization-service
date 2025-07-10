# News Summarization Service

## Overview

The News Summarization Service is a Django-based platform that fetches news articles from external sources (e.g., NewsAPI), stores them, and provides AI-powered summaries using OpenAI models via LangChain. The system exposes a REST API for managing users, articles, fetching new articles, and generating/retrieving summaries.

---

## Features
- **User Management:** Register, authenticate, and manage users (email-based login).
- **Article Management:** CRUD operations for news articles.
- **Fetching:** Periodic and manual fetching of articles from NewsAPI.
- **Summarization:** AI-powered summarization of articles using OpenAI models.
- **API Documentation:** Auto-generated with drf-spectacular (Swagger/OpenAPI).
- **Dockerized:** Full Docker setup for app, Postgres, Redis, Celery worker/beat/flower.
- **Dev Container:** VSCode devcontainer support for easy onboarding.

---

## Architecture

- **Django REST Framework** for API endpoints
- **Celery** for background tasks (fetching, summarization)
- **PostgreSQL** as the database
- **Redis** as the Celery broker
- **OpenAI (via LangChain)** for summarization

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- (For local dev) Python 3.10+ and PostgreSQL/Redis if not using Docker

### Environment Variables
Create a `.env` file in the project root with the following variables:
```
DB_HOST=db
DB_NAME=newsdb
DB_USER=newsuser
DB_PASS=newspass
NEWSAPI_API_KEY=your_newsapi_key
OPENAI_API_KEY=your_openai_key
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## Running with Docker

1. **Build and start all services:**
   ```sh
   docker-compose up --build
   ```
   This will start:
   - Django app (http://localhost:8000)
   - PostgreSQL (localhost:5432)
   - Redis (localhost:6379)
   - Celery worker, beat, and Flower (http://localhost:5555)

2. **Access the API docs:**
   - Swagger UI: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
   - OpenAPI schema: [http://localhost:8000/api/schema](http://localhost:8000/api/schema)

3. **Create a superuser (for admin access):**
   ```sh
   docker-compose exec app python manage.py createsuperuser
   ```

---


## API Endpoints

### Authentication
- `POST /api/users/create/` — Register a new user
- `POST /api/users/token/` — Obtain auth token
- `GET /api/users/me/` — Get current user info

### Articles
- `GET /api/articles/` — List articles
- `POST /api/articles/` — Create article (admin only)
- `GET /api/articles/{id}/` — Retrieve article
- `PUT /api/articles/{id}/` — Update article (admin only)
- `DELETE /api/articles/{id}/` — Delete article (admin only)
- `GET /api/articles/{id}/summary/` — Get/generate summary for article

### Fetchers
- `POST /api/fetchers/fetch/` — Manually trigger article fetch (admin only)

### Summarizer
- `POST /api/summarizer/summarize/` — Summarize an article by ID  (admin only)
- `GET /api/summarizer/article/{article_id}/summary/` — Get summary for article
- `GET /api/summarizer/article/{article_id}/summaries/` — Get all summaries for article
- `GET /api/summarizer/summary/{summary_id}/status/` — Get summary status

---

## Example API Requests & Responses

### 1. Register User
**Request:**
```http
POST /api/users/create/
Content-Type: application/json
{
  "email": "user@example.com",
  "name": "User Name",
  "password": "password123"
}
```
**Response:**
```json
{
  "email": "user@example.com",
  "name": "User Name"
}
```

### 2. Obtain Auth Token
**Request:**
```http
POST /api/users/token/
Content-Type: application/json
{
  "email": "user@example.com",
  "password": "password123"
}
```
**Response:**
```json
{
  "token": "<auth_token>"
}
```

### 3. List Articles
**Request:**
```http
GET /api/articles/
Authorization: Token <auth_token>
```
**Response:**
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Test Article",
      "content": "Some content...",
      "url": "http://example.com/article",
      "published_date": "2025-07-09T12:00:00Z",
      "author": "Author Name",
      "source": "Test Source",
      "image_url": null,
      "description": null,
      "news_client_source": "Test Client",
      "created_at": "2025-07-09T12:00:00Z"
    }
  ]
}
```

### 4. Summarize Article
**Request:**
```http
POST /api/summarizer/summarize/
Authorization: Token <admin_token>
Content-Type: application/json
{
  "article_id": 1,
  "ai_model": "gpt-4.1-nano",
  "max_words": 150
}
```
**Response:**
```json
{
  "success": true,
  "summary": {
    "id": 1,
    "article_id": 1,
    "article_title": "Test Article",
    "summary_text": "This is a summary...",
    "ai_model": "gpt-4.1-nano",
    "status": "completed",
    "word_count": 45,
    "tokens_used": 120,
    "created_at": "2025-07-09T12:01:00Z",
    "completed_at": "2025-07-09T12:01:05Z"
  }
}
```

### 5. Fetch Articles (Admin Only)
**Request:**
```http
POST /api/fetchers/fetch/
Authorization: Token <admin_token>
Content-Type: application/json
{
  "query_params": {"category": "technology"}
}
```
**Response:**
```json
{
  "message": "Fetch and save completed successfully."
}
```

---

## API Documentation
- **Swagger UI:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **OpenAPI schema:** [http://localhost:8000/api/schema](http://localhost:8000/api/schema)

---

## Development & Testing
- Run tests:
  ```sh
  python manage.py test
  ```
- Lint code:
  ```sh
  flake8
  ```

---

## Troubleshooting
- Ensure all environment variables are set (see `.env` example above).
- For Docker, ensure no port conflicts on 8000, 5432, 6379, 5555.
- If Celery tasks are not running, check the logs for `celery-worker` and `celery-beat` containers.

---

## License
MIT License

---

## Contact
Maintainer: Shachar Felman (<shaharfelmandev@gmail.com>) 