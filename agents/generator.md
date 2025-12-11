# Content Generator Agent

**Model:** `qwen2.5:3b` (quality writing)  
**Temperature:** 0.7 (creative output)

## Purpose

Creates comprehensive, SEO-optimized blog posts from research and source material.

## Capabilities

- Content writing
- RAG-based content grounding
- Article structuring
- File management

## Tools

- ScraperTool (content research)
- FileWriterTool (article saving)
- RAGTool (context retrieval)

## Output

- Well-structured markdown article
- Saved to `articles/` directory
- Slugified filename

## Usage

```python
from agents import create_generator
from tools import ScraperTool, FileWriterTool, RAGTool

generator = create_generator(
    tools=[ScraperTool(), FileWriterTool(), RAGTool()]
)
```
