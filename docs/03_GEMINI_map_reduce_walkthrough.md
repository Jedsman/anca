# GEMINI Map-Reduce Architecture Walkthrough

We have successfully implemented the "Editor-in-Chief" Hierarchical Map-Reduce architecture for ANCA. This new workflow allows for generating comprehensive, long-form articles by breaking the process down into specialized roles.

## Architecture Overview

The system uses `LangGraph` to orchestrate a team of agents:

```mermaid
graph TD
    UserInput(User Topic) --> Planner
    Planner(Planner<br/>Editor-in-Chief) -->|Blueprint| Researcher
    Researcher(Researcher<br/>Search & Ingest) -->|Ingested Context| Writers

    subgraph Map Phase
        Writers(Section Writers<br/>Parallel Execution)
    end

    Writers -->|Sections| Assembler
    Assembler(Assembler<br/>Final Editor) -->|Final Markdown| Output(Saved Article)
```

## Agents

1.  **Planner (`agents/planner.py`)**:

    - **Role**: Editor-in-Chief.
    - **Task**: Takes the topic and generates a structured `Blueprint` containing 5-7 sections, each with a heading, description, word count, and search queries.
    - **Output**: `Blueprint` object.

2.  **Researcher (`agents/researcher.py`)**:

    - **Role**: Research Assistant.
    - **Task**: Iterates through all search queries in the blueprint. Uses DuckDuckGo to find URLs, scrapes them (max 8 sources total), and populates the `RAGTool` (ChromaDB).
    - **Output**: Populated Vector DB.

3.  **Writer (`agents/writer.py`)**:

    - **Role**: Section Specialist.
    - **Task**: Runs in parallel for each section. Retrieves specific context from the RAG tool for its assigned section and writes the content.
    - **Output**: A formatted Markdown section.

4.  **Assembler (`agents/assembler.py`)**:
    - **Role**: Final Editor.
    - **Task**: Stitches all sections together, adds an introduction and conclusion, and saves the final file.
    - **Output**: Completed Article.

## Key Features

- **Map-Reduce Pattern**: Allows for unlimited article length scaling. Writers work in parallel (conceptually) and independent of each other's context window limits until assembly.
- **Multi-Provider Support**: Switch between AI providers easily.
  - **Gemini**: `gemini-2.0-flash-lite` (Default) with Rate Limiting (5 RPM).
  - **Groq**: `llama-3.3-70b-versatile` (Fast, high quality).
  - **Ollama**: `qwen2.5:7b-instruct` (Local, privacy-focused, zero cost).
- **Rate Limiting**: Built-in `TokenBucket` rate limiter to prevent 429 errors on free tiers.

## Usage

Run the workflow using `uv run python run_graph.py` with the desired arguments:

### 1. Default (Gemini 2.0 Flash Lite)

```bash
uv run python run_graph.py --topic "Future of AI Agents"
```

### 2. Run with Ollama (Local)

```bash
uv run python run_graph.py --topic "Benefits of Cold Brew Coffee" --provider ollama --model qwen2.5:7b-instruct
```

### 3. Run with Groq

```bash
uv run python run_graph.py --topic "Advanced Python Patterns" --provider groq --model llama-3.3-70b-versatile
```

## Project Structure

- `run_graph.py`: Main entry point and graph definition.
- `app/state.py`: Shared state schema (`ArticleState`).
- `agents/`: Agent implementations (`planner`, `researcher`, `writer`, `assembler`).
- `app/core/llm_wrappers.py`: `get_llm` factory and rate-limited wrappers.
- `app/core/rate_limiter.py`: Token bucket implementation.
