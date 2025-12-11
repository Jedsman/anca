# Model Experiments Log

**Purpose**: Track different models and approaches tested to solve the tool calling issue with the Content Generator agent.

**Hardware Constraint**: NVIDIA GTX 1070 (8GB VRAM)

---

## Problem Statement

The LangGraph Content Generator agent using Mistral 7B is not reliably calling the `save_article` tool, despite explicit instructions in the prompt file [prompts/generation_task.yaml](prompts/generation_task.yaml).

**Symptoms**:
- Agent generates the article content in its response text
- Agent calls `save_article` tool but with empty or minimal content parameter
- This appears to be a context/attention limitation in smaller models

---

## Experiments

### Experiment 1: Qwen2.5:7b-instruct (2025-12-10)

**Hypothesis**: Qwen2.5:7b has better tool calling capabilities than Mistral 7B while maintaining the same VRAM footprint.

**Changes Made**:
- ✅ Pulled `qwen2.5:7b-instruct` model via Ollama
- ✅ Updated [agents/generator.py:52](agents/generator.py#L52) to use `qwen2.5:7b-instruct`
- ✅ Updated [agents/researcher.py:32](agents/researcher.py#L32) to use `qwen2.5:7b-instruct`
- ✅ Updated [agents/auditor.py:31](agents/auditor.py#L31) to use `qwen2.5:7b-instruct`

**Status**: ✅ Partially Successful → Fixed

**Test Command**:
```bash
python run_graph.py
```

**Expected Outcome**:
- Agent successfully calls `save_article` with full content parameter
- Article is saved to a markdown file in the output directory

**Results**:
- ✅ **SUCCESS**: Generator called `save_article` with full content
- ✅ **SUCCESS**: Article saved to `homebrew-coffee.md`
- ⚠️ **ISSUE FOUND**: Auditor tried to read `homebrew-coffee-article` (wrong filename)
- ✅ **FIXED**: Added `filename` field to `AgentState` to pass between nodes
  - Modified [run_graph.py:51](run_graph.py#L51) to add `filename` to state
  - Modified [run_graph.py:133-143](run_graph.py#L133-L143) to extract filename from generator's tool call
  - Modified [run_graph.py:151-155](run_graph.py#L151-L155) to pass filename to auditor prompt

**Conclusion**: ✅ **Qwen2.5:7b-instruct successfully solved the tool calling issue!**
- Model reliably calls tools with correct parameters
- Much better than Mistral 7B for this use case
- Workflow communication improved with state-based filename passing

**Final Test (2025-12-10)**: ✅ **COMPLETE SUCCESS**
- Full workflow executed: Researcher → Generator → Auditor
- Article generated and saved correctly
- Auditor successfully read and analyzed the article
- **Output quality confirmed: Good quality documentation produced**

---

## Next Steps if Experiment 1 Fails

### Option A: Content Extraction Fallback
Implement middleware to detect empty tool calls and extract content from agent's response automatically.

### Option B: Split-Task Approach
Break generation into two steps:
1. "Generate and OUTPUT the article"
2. "Save the article from previous response"

### Option C: Try Smaller Quantization of Larger Model
Test `qwen2.5:14b-instruct-q4_K_M` if it fits in 8GB VRAM.

---

## References

- [AGENT_TOOL_CALLING_ISSUES.md](AGENT_TOOL_CALLING_ISSUES.md) - Previous investigation and analysis
- [prompts/generation_task.yaml](prompts/generation_task.yaml) - Current prompt configuration
- [run_graph.py](run_graph.py) - LangGraph workflow implementation
