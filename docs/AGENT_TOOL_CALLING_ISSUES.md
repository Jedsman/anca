# Agent Tool Calling Issues - Summary & Solutions

**Date:** 2025-12-09 23:38  
**Problem:** Agent calls `FileWriterTool` with empty `content` parameter despite explicit prompts

---

## What We've Tried

### 1. ✅ Explicit Prompts
- Added "DO NOT" warnings
- Provided correct/wrong examples
- Put critical instructions first
- Made step-by-step process

### 2. ✅ Pydantic Validation
- Fixed argument order (filename first, content second)
- Added field validators for edge cases
- Clear error messages

### 3. ✅ Content Validation
- Reject content < 50 words
- Reject content < 100 characters  
- Clear error feedback to agent

### 4. ✅ File Versioning
- Auto-backup before overwrite
- Prevents data loss

---

## Root Cause Analysis

The agent is exhibiting this behavior:

```
Agent Response:
"Here is the article:

# The Ultimate Guide to Homebrew Coffee

[... full 1500 word article here ...]

Now I will save it."

Tool Call:
FileWriterTool(filename="homebrew-coffee.md", content="")
```

**Why this happens:**
- LLMs are trained on conversational text first, tool calling second
- The model generates the article as **output text** naturally
- Then tries to call the tool, but doesn't "remember" to include the content
- This is a fundamental context/attention issue in smaller models

---

## Potential Solutions

### Option A: Use a Stronger Model (RECOMMENDED)
**Current:** `llama3.1:8b` (8 billion parameters)  
**Upgrade to:** `llama3.1:70b` or `qwen2.5:32b`

**Pros:**
- Much better at following complex instructions
- Better tool calling reliability
- Better context retention

**Cons:**
- Requires more VRAM (need model quantization)
- Slower inference

### Option B: Implement Content Extraction Fallback
Create a wrapper that:
1. Detects empty content
2. Extracts markdown from agent's last response
3. Uses that as the content parameter

**Pros:**
- Works around unreliable behavior
- No model change needed

**Cons:**
- Fragile (relies on parsing agent output)
- May extract wrong content
- Adds complexity

### Option C: Break Task Into Smaller Steps
Instead of one "generate" task, split into:
1. "Write the article and OUTPUT it"
2. "Take the article from your previous response and save it with FileWriter Tool"

**Pros:**
- Simpler for the model
- Explicit handoff reduces confusion

**Cons:**
- More tokens used
- More LLM calls
- Slower overall

### Option D: Use System-Level Extraction
Add middleware that:
- Captures all agent outputs
- When FileWriterTool is called with empty content
- Automatically extracts markdown from the last output
- Injects it as the content parameter

**Pros:**
- Invisible to agent
- Always works
- No prompt changes needed

**Cons:**
- Complex implementation
- May extract wrong content
- Hides the real problem

---

## My Recommendation

**Short term (this week):**
Try **Option C** - Split the task into explicit steps:
1. Research (current)
2. Generate article → OUTPUT the full markdown
3. Save article → READ the previous output and pass it to FileWriterTool
4. Audit
5. Revise

**Medium term (when ready):**
Try **Option A** - Test with `qwen2.5:14b` or `llama3.1:70b-q4` if you can offload enough layers

**Long term:**
If generating passive income content at scale, consider:
- Using commercial APIs (OpenAI GPT-4, Anthropic Claude)
- These have near-perfect tool calling
- Cost per article ~$0.10-0.50 vs. fighting local model issues

---

## Test Command for Option C

We can modify the generation task to explicitly output markdown first, then in a second step save it. Want me to implement this?

---

## Files Modified In This Session

1. `prompts/generation_task.yaml` - Ultra-explicit tool calling instructions
2. `prompts/research_task.yaml` - URL construction guidance
3. `prompts/revision_task.yaml` - Template variable fixes
4. `tools/file_writer_tool.py` - Versioning, validation, helpful errors
5. `tools/scraper_tool.py` - Pydantic field validator for keywords
6. `app/services/job_service.py` - Enhanced validation with fallback filename
7. `app/core/tool_call_logger.py` - Per-tool logging infrastructure
8. `app/core/llm_call_logger.py` - Request/response logging infrastructure

Total time invested: ~2 hours  
Core issue remaining: **LLM tool calling reliability**
