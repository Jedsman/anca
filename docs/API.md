# ANCA API Documentation

REST API for the Autonomous Niche Content Agent system.

## Quick Start

### Local Development

```bash
# Start API server
uv run uvicorn api:app --reload --port 8000

# Access API docs
open http://localhost:8000/docs
```

### Docker Deployment

```bash
# Build and start services
docker-compose up -d

# Pull required models
docker exec anca-ollama ollama pull llama3.1:8b
docker exec anca-ollama ollama pull llama3.1:8b
docker exec anca-ollama ollama pull mistral:7b

# Check status
docker-compose ps
curl http://localhost:8000/health
```

## API Endpoints

### POST /generate
Start content generation for a topic.

**Request:**
```json
{
  "topic": "home coffee brewing"
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "pending",
  "topic": "home coffee brewing",
  "created_at": "2025-12-08T16:00:00"
}
```

### GET /status/{job_id}
Check job status.

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "topic": "home coffee brewing",
  "created_at": "2025-12-08T16:00:00",
  "completed_at": "2025-12-08T16:15:00",
  "result": "Article generated successfully"
}
```

### GET /jobs
List all jobs.

### GET /articles
List all generated articles.

**Response:**
```json
{
  "articles": [
    {
      "filename": "best-coffee-brewing-methods.md",
      "size": 5432,
      "created": "2025-12-08T16:15:00",
      "modified": "2025-12-08T16:15:00"
    }
  ]
}
```

### GET /articles/{filename}
Download a specific article.

### DELETE /articles/{filename}
Delete a specific article.

### GET /health
Health check endpoint.

## Interactive Documentation

Access Swagger UI at: `http://localhost:8000/docs`

## Example Usage

```bash
# Generate content
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "home coffee brewing"}'

# Check status
curl http://localhost:8000/status/YOUR-JOB-ID

# List articles
curl http://localhost:8000/articles

# Download article
curl http://localhost:8000/articles/your-article.md -o article.md
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  FastAPI    │────▶│   Ollama     │
│   (ANCA)    │     │  (LLM Models)│
└──────┬──────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│  CrewAI     │
│  Workflow   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Articles   │
│  Storage    │
└─────────────┘
```

## Environment Variables

See `.env.production` for configuration options.

## Deployment Notes

- Ollama requires ~8GB RAM for 3B models
- Mistral 7B requires ~16GB RAM
- Content generation takes 5-15 minutes per article
- Use background tasks for async processing
