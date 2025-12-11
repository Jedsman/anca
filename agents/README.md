# ANCA Agents

Multi-agent system for autonomous content creation.

## Agents

### [Market Researcher](researcher.md)

- **Model**: llama3.1:8b
- **Role**: Keyword research and topic discovery
- **Stage**: 2

### [Content Generator](generator.md)

- **Model**: qwen2.5:3b
- **Role**: Article writing with RAG
- **Stage**: 2 (enhanced in Stage 3)

### [SEO Auditor](auditor.md)

- **Model**: mistral:7b
- **Role**: Quality evaluation and feedback
- **Stage**: 3

## Workflow

```
Researcher → Generator → Auditor
    ↓           ↓           ↓
 Keyword    Article    Feedback
```

## Usage

```python
from agents import create_researcher, create_generator, create_auditor

# Initialize agents
researcher = create_researcher(tools=[scraper])
generator = create_generator(tools=[scraper, writer, rag])
auditor = create_auditor(tools=[])
```

See individual agent docs for details.
