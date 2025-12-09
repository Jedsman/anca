# ANCA Tools

Specialized tools for web scraping, file operations, and RAG.

## Tools

### [ScraperTool](scraper_tool.md)
- **Purpose**: Ethical web scraping
- **Stage**: 1
- **Features**: Robots.txt, caching, chunking

### [FileWriterTool](file_writer_tool.md)
- **Purpose**: Article file management
- **Stage**: 1
- **Features**: Auto directory creation, UTF-8

### [RAGTool](rag_tool.md)
- **Purpose**: Vector storage and retrieval
- **Stage**: 3
- **Features**: ChromaDB, semantic search

## Usage

```python
from tools import ScraperTool, FileWriterTool, RAGTool

# Initialize tools
scraper = ScraperTool()
writer = FileWriterTool()
rag = RAGTool()

# Use with agents
from agents import create_generator

generator = create_generator(
    tools=[scraper, writer, rag]
)
```

See individual tool docs for details.
