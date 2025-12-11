# Topic Discovery Agent Implementation Plan

## Goal

Create a **Topic Discovery Agent** that autonomously identifies high-potential content topics (long-tail keywords) before the content generation workflow begins.

## Background

Currently, topics are manually specified via `--topic`. The ANCA architecture envisions the Market Researcher discovering topics automatically. This agent will fill that gap.

---

## Proposed Changes

### New Tools

#### [NEW] `tools/keyword_tool.py`

Implements three free keyword discovery strategies (no API keys required):

| Tool Function                    | Description                                                  |
| -------------------------------- | ------------------------------------------------------------ |
| `google_autocomplete(seed: str)` | Scrapes Google's autocomplete suggestions for a seed keyword |
| `related_searches(seed: str)`    | Extracts "Related Searches" from DuckDuckGo results          |
| `extract_keywords(text: str)`    | Uses YAKE/KeyBERT to extract keywords from scraped content   |

---

### New Agent

#### [NEW] `agents/topic_discoverer.py`

A new LangGraph agent that:

1. Takes a **seed niche** (e.g., "coffee brewing")
2. Expands it into 10-20 specific topic candidates using the keyword tools
3. Filters/ranks topics by specificity and potential (prefers long-tail, question-based)
4. Outputs a prioritized list of topics

```
Input: "coffee brewing"
Output: [
  "how to brew coffee with a french press",
  "best water temperature for pour over coffee",
  "common cold brew coffee mistakes",
  ...
]
```

---

### New Prompt

#### [NEW] `prompts/topic_discovery_task.yaml`

Prompt instructing the agent to:

- Use autocomplete and related search tools
- Prefer question-based, long-tail keywords (5+ words)
- Output exactly N topics as a numbered list

---

### Workflow Integration

#### [MODIFY] `run_graph.py`

Add optional `--discover` mode:

```bash
# Current: manual topic
python run_graph.py --topic "how to brew coffee at home"

# New: auto-discover topics from seed
python run_graph.py --discover "coffee brewing" --count 5
```

When `--discover` is used:

1. Run Topic Discovery Agent first
2. Loop through discovered topics, running the full workflow for each

---

## Open Questions

1. **Integration approach:** Should the agent run as a separate CLI mode (`--discover "seed"`) or be integrated as the first node in the main graph?

2. **Limitation:** Free tools can't provide search volume/competition data. Topics will be ranked by heuristics (question format, length, specificity) rather than actual SEO metrics.

---

## Implementation Order

1. `tools/keyword_tool.py` - Core keyword discovery functions
2. `prompts/topic_discovery_task.yaml` - Agent prompt
3. `agents/topic_discoverer.py` - Agent implementation
4. `run_graph.py` modifications - CLI integration
5. Manual testing & iteration
