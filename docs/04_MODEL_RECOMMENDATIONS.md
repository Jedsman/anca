# Optimized Model Selection for ANCA

Based on research into **Groq API** capabilities and **8GB VRAM** constraints for local Ollama execution, here is the recommended model mapping for each agent.

## Strategy

- **Groq**: Use the largest available model (`llama-3.3-70b`) for complex tasks (Planning, Auditing) and faster models (`llama-3.1-8b`) for simple tasks if speed is critical (though 70B is very fast on Groq).
- **Ollama (8GB VRAM)**: We must stay under ~6-7GB model size to leave room for context.
  - **Best All-Rounder**: `qwen2.5:7b-instruct` (Fast, smart, 4.5GB).
  - **Best Reasoning**: `mistral-nemo:12b-instruct-q4_K_M` (~7.5GB, tight but doable) or `gemma2:9b-instruct-q5_K_M` (~6.5GB).
  - **Best Speed**: `phi4` or `llama3.1:8b`.

## Model Recommendation Matrix

| Agent              | Role                        | Recommended Groq Model    | Recommended Ollama Model (8GB VRAM)                      | Rationale                                                                 |
| :----------------- | :-------------------------- | :------------------------ | :------------------------------------------------------- | :------------------------------------------------------------------------ |
| **Planner**        | Editor-in-Chief (Structure) | `llama-3.3-70b-versatile` | `mistral-nemo:12b-instruct-q4_K_M`                       | Needs high instruction following and strict output formatting (JSON/XML). |
| **Trend Analyzer** | Idea Scout                  | `llama-3.3-70b-versatile` | `gemma2:9b-instruct-q5_K_M`                              | Needs creative reasoning to find "niche" intersections.                   |
| **Researcher**     | Search & Ingest             | `llama-3.1-8b-instant`    | `qwen2.5:7b-instruct`                                    | Simple query generation tasks; speed is priority.                         |
| **Writer**         | Content Generator           | `llama-3.3-70b-versatile` | `qwen2.5:7b-instruct` (or `mistral-nemo` if VRAM allows) | Needs long context retention and prose quality.                           |
| **Assembler**      | Final Editor                | `llama-3.3-70b-versatile` | `qwen2.5:7b-instruct`                                    | Needs to process large token counts (full article) effectively.           |
| **Fact Checker**   | Truth Verifier              | `llama-3.3-70b-versatile` | `gemma2:9b-instruct-q5_K_M`                              | Needs high "world knowledge" accuracy to detect hallucinations.           |
| **Auditor**        | SEO & Quality               | `llama-3.3-70b-versatile` | `mistral-nemo:12b-instruct-q4_K_M`                       | Needs strong critical reasoning to find nuanced flaws.                    |
| **Refiner**        | Fixer                       | `llama-3.3-70b-versatile` | `qwen2.5:7b-instruct`                                    | Needs to follow "Humanize" instructions strictly.                         |

## Quick Apply

### 1. Groq Configuration

No action needed if using `llama-3.3-70b-versatile` as default, but we can fine-tune `run_graph.py` to use `llama-3.1-8b-instant` for just the **Researcher** to save tokens/time.

### 2. Ollama Setup

Run these commands to pull the optimized local models:

```powershell
ollama pull qwen2.5:7b-instruct
ollama pull mistral-nemo:12b-instruct-q4_K_M
ollama pull gemma2:9b-instruct-q5_K_M
```

_Note: If `mistral-nemo` OOMs (Out of Memory), fallback to `qwen2.5:7b-instruct` for all roles._
