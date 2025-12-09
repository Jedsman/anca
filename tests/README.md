# ANCA Testing Suite

Isolated test scripts for debugging and validation.

## Tool Tests

### ScraperTool
```bash
uv run python tests/test_scraper_isolated.py
```
Tests web scraping, caching, and content formatting.

### FileWriterTool
```bash
uv run python tests/test_file_writer_isolated.py
```
Tests file writing, directory creation, and error handling.

## Agent Tests

### Researcher Agent
```bash
uv run python tests/test_researcher_isolated.py
```
Tests keyword research agent with simple task.

### Generator Agent
```bash
uv run python tests/test_generator_isolated.py
```
Tests content generation agent with pre-defined input.

## Integration Test

### Full Workflow
```bash
uv run python tests/test_integration.py
```
Tests Researcher → Generator pipeline with simplified tasks.

## Test Strategy

**Isolation levels:**
1. **Tools** - Test without agents
2. **Agents** - Test with simple tasks
3. **Integration** - Test full workflow

**Benefits:**
- Fast debugging
- Identify bottlenecks
- Validate each component
- Reduce test time
