# Testing Guide for ANCA Fixes

This document explains how to test the fixes applied to resolve the API vs UV execution differences.

## What Was Fixed

### 1. **Ollama Connection & Health Checks**
- Added health checks to ensure Ollama is ready before API starts
- Fixed dependency ordering in docker-compose
- Added proper service conditions

### 2. **Model Verification**
- Enhanced pull_models.sh to verify each model after pulling
- Added startup checks to verify all required models are available
- Added logging for model selection in each agent

### 3. **Environment Variables**
- Added all necessary environment variables to docker-compose
- Fixed OLLAMA_BASE_URL configuration for Docker networking

### 4. **Job Validation**
- Added validation to check if articles were actually created
- Verify article file exists and has sufficient content
- Check for signs of actual work (sources, URLs, etc.)

### 5. **Logging Configuration**
- Separated logging setup for standalone vs API execution
- UV runs log to `anca_1.log`, API logs to `anca.log`
- Fixed logging conflicts when run_crew.py is imported

### 6. **Debugging & Monitoring**
- Added model selection logging in all agent factories
- Added Ollama connectivity checks on API startup
- Enhanced error reporting and validation

---

## Testing Steps

### Step 1: Rebuild Docker Containers

```bash
# Stop existing containers
docker-compose down

# Rebuild with new changes
docker-compose build --no-cache

# Start services
docker-compose up
```

### Step 2: Monitor Startup

Watch the logs to verify:

```bash
docker-compose logs -f anca
```

Look for:
- ✓ Ollama connectivity check passes
- ✓ All three models are available (llama3.1:8b, llama3.1:8b, mistral:7b)
- ✓ Agent creation logs showing correct models

Example expected output:
```
anca-api | INFO - Checking Ollama connectivity at http://ollama:11434
anca-api | INFO - ✓ Ollama connected successfully. Available models: ['llama3.1:8b', 'llama3.1:8b', 'mistral:7b']
anca-api | INFO - ✓ All required models are available
anca-api | INFO - Creating Researcher agent with model: ollama/llama3.1:8b at http://ollama:11434
anca-api | INFO - Creating Generator agent with model: ollama/llama3.1:8b at http://ollama:11434
anca-api | INFO - Creating Auditor agent with model: ollama/mistral:7b at http://ollama:11434
```

### Step 3: Test Model Puller

Check that models were pulled successfully:

```bash
# View model puller logs
docker-compose logs model-puller

# Verify models in Ollama
docker exec anca-ollama ollama list
```

### Step 4: Test API Endpoint

```bash
# Test health endpoint
curl http://localhost:8000/health

# Create a test job
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "homebrew coffee"}'

# Get job status (replace JOB_ID with actual ID from previous response)
curl http://localhost:8000/api/v1/jobs/JOB_ID
```

### Step 5: Compare Logs

After the job completes, compare the logs:

```bash
# View API execution logs
cat logs/anca.log

# Compare with previous UV run
cat logs/anca_1.log
```

### Step 6: Verify Job Validation

The API should now:
1. Check if article file was created
2. Verify file has sufficient content (>500 chars)
3. Look for evidence of scraping (sources, URLs)
4. Mark as FAILED if validation fails

Check job status:
```bash
curl http://localhost:8000/api/v1/jobs/JOB_ID
```

If validation failed, you'll see:
```json
{
  "status": "FAILED",
  "error": "Validation failed: Article file not found: homebrew-coffee.md"
}
```

---

## Debugging Commands

### Check Ollama Connectivity from API Container

```bash
docker exec anca-api curl http://ollama:11434/api/tags
```

### View Available Models

```bash
docker exec anca-ollama ollama list
```

### Test Model Directly

```bash
docker exec anca-ollama ollama run llama3.1:8b "Hello, test"
```

### Check Container Networking

```bash
# Verify containers can communicate
docker exec anca-api ping -c 3 ollama

# Check DNS resolution
docker exec anca-api nslookup ollama
```

### View Real-Time Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f anca
docker-compose logs -f ollama
```

### Restart Specific Service

```bash
# Restart API only
docker-compose restart anca

# Restart Ollama
docker-compose restart ollama
```

---

## Expected Behavior After Fixes

### ✅ **Successful Execution Should Show:**

1. **Agent Creation Logs:**
   ```
   Creating Researcher agent with model: ollama/llama3.1:8b at http://ollama:11434
   Creating Generator agent with model: ollama/llama3.1:8b at http://ollama:11434
   Creating Auditor agent with model: ollama/mistral:7b at http://ollama:11434
   ```

2. **Scraper Activity:**
   ```
   Starting scrape for https://duckduckgo.com/?q=homebrew+coffee
   Successfully scraped URL: X chunks created
   Cached content for URL
   ```

3. **Multiple LLM Calls:**
   - 20+ LiteLLM log entries (not just 5)
   - Calls to all three models

4. **Job Validation:**
   ```
   Job XXX: Validated article homebrew-coffee.md (XXXX characters)
   Job XXX completed successfully with validation
   ```

5. **Article Creation:**
   - File exists in `articles/` directory
   - File has substantial content (>500 characters)
   - Contains research, sources, and well-structured content

### ❌ **Failure Indicators:**

1. **Connection Issues:**
   ```
   ✗ Failed to connect to Ollama at http://ollama:11434
   ```

2. **Missing Models:**
   ```
   ✗ Missing required models: ['mistral:7b']
   ```

3. **Validation Failures:**
   ```
   Job XXX validation failed: Article file not found
   Job XXX validation failed: Result output is too short
   ```

4. **No Scraping Activity:**
   - Logs show no scraper tool activity
   - Job completes too quickly (<3 minutes)

---

## Rollback Plan

If issues persist:

```bash
# Stop all services
docker-compose down

# Remove volumes to start fresh
docker-compose down -v

# Check out previous version
git checkout HEAD~1

# Restart
docker-compose up --build
```

---

## Performance Comparison

| Metric | Old API (Broken) | New API (Fixed) | UV (Reference) |
|--------|-----------------|-----------------|----------------|
| **Execution Time** | ~2:38 min | ~5-10 min | ~5-10 min |
| **LLM Calls** | 5 | 20+ | 20+ |
| **Scraping** | None | Multiple URLs | Multiple URLs |
| **Article Size** | 0-500 chars | 2000+ chars | 2000+ chars |
| **Validation** | False positive | Accurate | N/A |

---

## Troubleshooting

### Problem: Ollama health check fails

**Solution:**
```bash
# Check if Ollama is running
docker ps | grep ollama

# Check Ollama logs
docker logs anca-ollama

# Restart Ollama
docker-compose restart ollama
```

### Problem: Models not found

**Solution:**
```bash
# Re-run model puller
docker-compose up model-puller

# Or pull manually
docker exec anca-ollama ollama pull llama3.1:8b
docker exec anca-ollama ollama pull llama3.1:8b
docker exec anca-ollama ollama pull mistral:7b
```

### Problem: Job validation always fails

**Solution:**
```bash
# Check if articles directory is mounted correctly
docker exec anca-api ls -la /app/articles

# Check file permissions
docker exec anca-api ls -l /app/articles

# Verify volume mount
docker inspect anca-api | grep -A 10 Mounts
```

### Problem: Different models being used

**Solution:**
- Check agent creation logs for model names
- Verify OLLAMA_BASE_URL is set correctly
- Check if models are available in Ollama
- Review LiteLLM logs for actual model being called

---

## Additional Monitoring

### View Job Service Logs

```python
# In Python shell
from app.services.job_service import job_service
jobs = job_service.list_jobs()
for job in jobs:
    print(f"{job.job_id}: {job.status} - {job.error}")
```

### Check ChromaDB

```bash
# View ChromaDB contents
docker exec anca-api ls -la /app/.chroma
```

### Monitor Resource Usage

```bash
# Check container resource usage
docker stats anca-api anca-ollama
```

---

## Success Criteria

The fixes are successful when:

1. ✅ API execution matches UV execution behavior
2. ✅ All three models are used correctly
3. ✅ Scraping occurs and content is retrieved
4. ✅ Articles are created with substantial content
5. ✅ Job validation accurately reflects completion
6. ✅ No false positives for "completed successfully"
7. ✅ Logs show detailed execution trace
8. ✅ Execution time is comparable (5-10 minutes)

---

## Next Steps

After confirming fixes work:

1. Run multiple test topics to ensure consistency
2. Monitor production jobs for any edge cases
3. Consider adding metrics/monitoring dashboard
4. Implement job timeout handling
5. Add retry logic for transient failures
