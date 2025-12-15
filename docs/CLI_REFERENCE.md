# ANCA CLI Reference

The interface for running the ANCA workflow is `run_graph.py`.

## Basic Usage

```bash
uv run python run_graph.py [OPTIONS]
```

## Arguments

| Argument           | Type   | Default                    | Description                                                                                                            |
| :----------------- | :----- | :------------------------- | :--------------------------------------------------------------------------------------------------------------------- |
| `--topic`          | `str`  | `""`                       | The specific topic to write an article about.                                                                          |
| `--provider`       | `str`  | `"gemini"`                 | LLM Provider to use. Options: `gemini`, `groq`, `ollama`.                                                              |
| `--model`          | `str`  | `gemini-flash-lite-latest` | Specific model name within the provider.                                                                               |
| `--niche`          | `str`  | `""`                       | A broad niche (e.g., "AI Law") for targeted trend discovery.                                                           |
| `--discover`       | `flag` | `False`                    | Enable "Scout Mode" to find trending topics automatically.                                                             |
| `--only-discovery` | `flag` | `False`                    | Halt execution after finding a topic (useful for testing/review).                                                      |
| `--interactive`    | `flag` | `False`                    | Present a list of candidate topics and ask user to select one.                                                         |
| `--affiliate`      | `flag` | `False`                    | Enable **Affiliate Marketing Mode**. Focuses on "Buyer's Guides", high commercial intent, and inserts affiliate links. |

## Common Workflows

### 1. Manual Topic (Standard Run)

Write an article about a specific topic you already have in mind.

```bash
uv run python run_graph.py --topic "The Future of Quantum Computing"
```

### 2. Scout Mode (Global Discovery)

Let the agent find a "Rising Star" trend from global news/search and write about it.

```bash
uv run python run_graph.py --discover
```

### 3. Niche Discovery (Targeted)

Find a trending topic within a specific industry.

```bash
uv run python run_graph.py --niche "Sustainable Coffee"
```

### 4. Interactive Selection (Recommended)

The agent generates 10 candidate topics, and you choose the best one.

```bash
uv run python run_graph.py --discover --interactive
```

### 5. Affiliate Marketing Mode (Money Generation)

Finds high-ticket products, writes a "Buyer's Guide", and adds affiliate placeholders.

```bash
uv run python run_graph.py --discover --interactive --affiliate
```

### 6. Local LLM (Ollama)

Run entirely locally (requires Ollama to be running).

```bash
uv run python run_graph.py --topic "Local AI Models" --provider ollama --model qwen2.5:7b-instruct
```

### 7. Groq (High Speed)

Use Groq for ultra-fast generation.

```bash
uv run python run_graph.py --discover --provider groq --model llama-3.3-70b-versatile
```
