# RAGTool

**Stage:** 3  
**Type:** Vector storage and retrieval

## Purpose
Stores scraped content in ChromaDB for semantic search and retrieval.

## Features
- **ChromaDB integration** - Persistent vector storage
- **Automatic embeddings** - sentence-transformers
- **Semantic search** - Find relevant content by meaning
- **Metadata tracking** - Preserves source info

## Storage
Data stored in `.chroma/` directory (persistent).

## Usage

### Ingest Content
```python
from tools import RAGTool

rag = RAGTool()
chunks = [
    {
        'content': 'Text content here...',
        'metadata': {'url': 'https://...', 'chunk_index': 0}
    }
]
rag.ingest(chunks)
```

### Retrieve Content
```python
result = rag.retrieve(
    query="What is the best grind size?",
    n_results=5
)
# Returns formatted string with top 5 relevant chunks
```

## Output Format
```
# Retrieved Content for: query

## Result 1
Source: URL
Chunk: 1/3

[relevant content...]
```
