# Agentic Starter Repo

This repository provides a robust, generic foundation for building agentic AI systems using LangGraph and Ollama.

It implements a "Researcher -> Writer -> Reviewer" workflow that can be easily adapted for any content generation or research task.

## Features

- **LangGraph Workflow**: State-of-the-art agent orchestration.
- **Generic Agents**: Configurable Researcher, Writer, and Reviewer agents.
- **Tool-First Design**: Agents utilize tools (Search, Scraper, File I/O, RAG) effectively.
- **RAG Integration**: Built-in simple RAG system for context retrieval.
- **Ollama Support**: Optimized for local LLMs (Qwen, Llama 3, etc.).

## Quick Start with UV

This project uses `uv` for lightning-fast dependency management.

1.  **Install dependencies**:

    ```bash
    uv sync
    ```

2.  **Setup Environment**:

    Copy `.env.example` to `.env` and configure your keys (e.g., `SERPER_API_KEY` for search).

    ```bash
    cp .env.example .env
    ```

3.  **Run the Workflow**:
    ```bash
    uv run python main.py --topic "The Future of AI Agents"
    ```

## Customization

- **Prompts**: Edit the YAML files in `prompts/` to change agent behavior.
- **Workflow**: Modify `main.py` to add/remove nodes or change the graph structure.
- **Tools**: Add new tools in the `tools/` directory and register them in `main.py`.

## Directory Structure

- `agents/`: Agent definitions (LangGraph nodes).
- `prompts/`: System prompts for each agent.
- `tools/`: Tool implementations.
- `main.py`: Main entry point and workflow definition.
