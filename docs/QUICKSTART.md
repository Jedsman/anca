# ANCA Quick Start Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 8GB RAM available
- 20GB disk space for models

### Start the System

```bash
# Clone or navigate to the project
cd anca

# Start all services (first time will pull models - takes 10-20 minutes)
docker-compose up --build

# Wait for the startup messages:
# ✓ Ollama connected successfully
# ✓ All required models are available
# ✓ Creating agents...
```

### Test the API

```bash
# Check health
curl http://localhost:8000/health

# Generate an article
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "homebrew coffee"}'

# Response will include a job_id:
# {"job_id": "xxx-xxx-xxx", "status": "PENDING", ...}

# Check job status (replace JOB_ID)
curl http://localhost:8000/api/v1/jobs/JOB_ID

# List all jobs
curl http://localhost:8000/api/v1/jobs
```

### Monitor Execution

```bash
# Watch logs in real-time
docker-compose logs -f anca

# Look for:
# - Agent creation with correct models
# - Scraping activity
# - Multiple LLM calls
# - Validation messages
```

### View Results

```bash
# Check generated articles
ls -lh articles/

# Read an article
cat articles/homebrew-coffee.md
```

---

## 📊 What to Expect

### Successful Execution

**Timing:**
- Job creation: Instant
- Execution: 5-10 minutes
- Total: ~10 minutes

**Logs should show:**
```
Creating Researcher agent with model: ollama/llama3.1:8b at http://ollama:11434
Creating Generator agent with model: ollama/llama3.1:8b at http://ollama:11434
Creating Auditor agent with model: ollama/mistral:7b at http://ollama:11434
Starting scrape for https://duckduckgo.com/?q=homebrew+coffee
Successfully scraped URL: 1 chunks created
Starting scrape for https://www.example.com/...
Successfully scraped URL: 4 chunks created
Job XXX: Validated article homebrew-coffee.md (2847 characters)
Job XXX completed successfully with validation
```

**Job Status:**
```json
{
  "job_id": "xxx",
  "status": "COMPLETED",
  "topic": "homebrew coffee",
  "result": "Article written to: homebrew-coffee.md\nSources used: 3",
  "error": null
}
```

**Article:**
- Located in `articles/homebrew-coffee.md`
- 2000+ characters
- Well-structured with headings
- Contains research from multiple sources
- SEO-optimized

---

## 🔧 Troubleshooting

### Problem: "Failed to connect to Ollama"

```bash
# Check if Ollama is running
docker ps | grep ollama

# View Ollama logs
docker logs anca-ollama

# Restart Ollama
docker-compose restart ollama

# Wait for health check to pass
docker-compose logs -f ollama
```

### Problem: "Missing required models"

```bash
# Re-run model puller
docker-compose up model-puller

# Or pull manually
docker exec anca-ollama ollama pull llama3.1:8b
docker exec anca-ollama ollama pull llama3.1:8b
docker exec anca-ollama ollama pull mistral:7b

# Verify models
docker exec anca-ollama ollama list
```

### Problem: Job validation fails

```bash
# Check if articles directory exists
ls -la articles/

# Check volume mount
docker exec anca-api ls -la /app/articles

# View detailed logs
docker-compose logs anca | grep -i validation
```

### Problem: Job takes too long or hangs

```bash
# Check if models are responding
docker exec anca-ollama ollama run llama3.1:8b "test"

# Check resource usage
docker stats anca-api anca-ollama

# View real-time logs
docker-compose logs -f anca
```

---

## 🧪 Testing Different Topics

```bash
# Test with different topics
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "gardening tips for beginners"}'

curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "best practices for remote work"}'

curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "healthy meal prep ideas"}'
```

---

## 📁 Directory Structure

```
anca/
├── articles/          # Generated articles (mounted volume)
├── logs/              # Application logs (mounted volume)
├── .cache/            # Scraper cache (mounted volume)
├── .chroma/           # ChromaDB vector store (mounted volume)
├── agents/            # Agent definitions
├── tools/             # Custom tools (scraper, RAG, etc.)
├── app/               # FastAPI application
│   ├── api/           # API routes
│   ├── core/          # Configuration
│   ├── schemas/       # Pydantic models
│   └── services/      # Business logic
├── docker-compose.yml # Docker orchestration
├── Dockerfile.api     # API container
├── pull_models.sh     # Model pulling script
├── run_crew.py        # Standalone crew runner
├── TESTING.md         # Detailed testing guide
└── FIXES_SUMMARY.md   # Summary of fixes applied
```

---

## 🔍 Useful Commands

### Docker Commands

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Rebuild containers
docker-compose build --no-cache

# View logs
docker-compose logs -f [service]

# Execute command in container
docker exec -it anca-api bash

# Check resource usage
docker stats
```

### API Commands

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Create job
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "your topic"}'

# Get job status
curl http://localhost:8000/api/v1/jobs/{job_id}

# List all jobs
curl http://localhost:8000/api/v1/jobs

# List articles
curl http://localhost:8000/api/v1/articles

# Get article content
curl http://localhost:8000/api/v1/articles/{filename}
```

### Model Management

```bash
# List models
docker exec anca-ollama ollama list

# Pull a model
docker exec anca-ollama ollama pull llama3.1:8b

# Remove a model
docker exec anca-ollama ollama rm llama3.1:8b

# Test a model
docker exec anca-ollama ollama run llama3.1:8b "Hello"

# Check Ollama API
curl http://localhost:11434/api/tags
```

### Log Management

```bash
# View API logs
tail -f logs/anca.log

# View UV execution logs
tail -f logs/anca_1.log

# Search logs
grep -i "error" logs/anca.log
grep -i "validation" logs/anca.log

# Clear logs
> logs/anca.log
```

---

## 🎯 Success Indicators

### ✅ System is Healthy When:

1. Health endpoint returns 200:
   ```bash
   curl -s http://localhost:8000/health | jq .
   ```

2. All models are available:
   ```bash
   docker exec anca-ollama ollama list
   # Should show: llama3.1:8b, llama3.1:8b, mistral:7b
   ```

3. Logs show agent creation:
   ```bash
   docker-compose logs anca | grep "Creating.*agent"
   ```

4. Jobs complete with validation:
   ```bash
   curl http://localhost:8000/api/v1/jobs | jq '.[] | {status, error}'
   ```

5. Articles are generated:
   ```bash
   ls -lh articles/
   ```

---

## 🛠️ Development Mode

### Run with UV (Without Docker)

```bash
# Install dependencies
uv sync

# Run standalone
uv run python run_crew.py

# Check logs
tail -f logs/anca_1.log

# Check generated article
ls -lh articles/
```

### Run API Locally

```bash
# Install dependencies
uv sync

# Set environment
export OLLAMA_BASE_URL=http://localhost:11434

# Run API
uv run uvicorn app.main:app --reload --port 8000

# Test
curl http://localhost:8000/health
```

---

## 📚 Additional Resources

- **Detailed Testing Guide:** [TESTING.md](TESTING.md)
- **Fixes Summary:** [FIXES_SUMMARY.md](FIXES_SUMMARY.md)
- **API Documentation:** http://localhost:8000/docs (when running)
- **CrewAI Docs:** https://docs.crewai.com/

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs:**
   ```bash
   docker-compose logs anca
   docker-compose logs ollama
   ```

2. **Verify setup:**
   ```bash
   curl http://localhost:8000/health
   docker exec anca-ollama ollama list
   ```

3. **Review documentation:**
   - [TESTING.md](TESTING.md) - Comprehensive testing guide
   - [FIXES_SUMMARY.md](FIXES_SUMMARY.md) - What was fixed and why

4. **Check common issues:**
   - Ollama not responding → Restart Ollama service
   - Models missing → Re-run model-puller
   - Job validation fails → Check articles directory
   - Logs show errors → Check specific error messages

---

## 🔄 Clean Restart

If things get messy:

```bash
# Stop everything
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up
```

---

## 📈 Next Steps

Once the system is working:

1. **Experiment with topics:**
   - Try different niches
   - Test various keyword types
   - Explore content depth

2. **Customize agents:**
   - Modify agent prompts in `agents/`
   - Adjust model parameters
   - Add new tools

3. **Monitor performance:**
   - Track execution times
   - Review article quality
   - Optimize model selection

4. **Scale up:**
   - Add more agents
   - Implement job queuing
   - Set up production deployment

Happy content generating! 🎉
