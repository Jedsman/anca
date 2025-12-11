# Prompt Engineering Fixes - Summary

**Date:** 2025-12-09 22:45  
**Status:** Complete

---

## What Was Fixed

### 1. Template Variable Errors ✅

**Problem:** CrewAI was trying to interpolate `{topic-slug}` and `{topic}` in code examples as template variables.

**Files Fixed:**
- `prompts/research_task.yaml` - Changed `{topic-slug}` to `[topic-slug]` in URL examples
- `prompts/generation_task.yaml` - Changed `{topic}` to `[your topic]` in RAGTool examples
- `prompts/revision_task.yaml` - Changed `{topic}` to `[the topic]` in RAGTool examples

**Result:** No more "Template variable not found" errors.

---

### 2. Pydantic Validation Error (ScraperTool) ✅

**Problem:** Agent was passing string `'None'` instead of actual `None` for the `keywords` parameter.

**Error:**
```
Arguments validation failed: 1 validation error for ScraperToolSchema
keywords
  Input should be a valid list [type=list_type, input_value='None', input_type=str]
```

**Fix:** Added `field_validator` to `ScraperToolSchema`:
```python
@field_validator('keywords', mode='before')
@classmethod
def sanitize_keywords(cls, v):
    if isinstance(v, str) and v.lower() in ('none', 'null', ''):
        return None
    return v
```

**File:** `tools/scraper_tool.py`

---

### 3. Empty File Detection ✅

**Problem:** Agent was claiming success ("Article written to: X") but not actually calling `FileWriterTool`, resulting in empty files.

**Fixes:**

**A. Strengthened Prompt** (`prompts/generation_task.yaml`):
```yaml
## ⚠️ STEP 4: SAVE THE ARTICLE (MANDATORY) ⚠️

**YOU MUST CALL THIS TOOL TO SAVE YOUR WORK.**

Do NOT just write the article in your response. You MUST call:

❌ WRONG: Writing the article in your response without calling the tool
✅ CORRECT: Calling FileWriterTool with the full article as the content parameter

**If you do not call FileWriterTool, your work will be LOST.**
```

**B. Added Validation Safeguards** (`app/services/job_service.py`):
```python
def _validate_job_completion(self, job_id: str, result_str: str, topic: str = None):
    # Multiple filename extraction patterns
    # Fallback filename construction from topic
    # Empty file detection
    # Minimum word count check (200 words)
    # Clear error messages: "Agent did not save content correctly"
```

---

### 4. Model Upgrade ✅

**Changed:** Generator model from `qwen2.5:3b` → `llama3.1:8b`

**Reason:** 3B model too weak for 1500+ word article generation

**Files:**
- `agents/generator.py` - Line 25
- `pull_models.sh` - Removed qwen2.5:3b
- `app/main.py` - Updated required models list

---

## Testing Status

### What Works:
✅ Research agent finds URLs correctly (observed scraping homegrounds.co, perfectdailygrind.com)
✅ Template variables no longer cause crashes
✅ Pydantic validation handles edge cases
✅ Job validation detects empty files

### What Needs Testing:
⚠️ Full end-to-end run with the new prompts and safeguards
⚠️ Verify FileWriterTool is actually called by the agent
⚠️ Verify revision loop works correctly

---

## Next Steps

1. **Run a clean test:**
   ```bash
   rm -f articles/*.md
   OLLAMA_NUM_CTX=8192 uv run python run_crew.py
   ```

2. **Check for output:**
   ```bash
   ls -lh articles/
   wc -w articles/homebrew-coffee.md
   ```

3. **Review logs for any remaining errors**

---

## Known Limitations

1. **Agent reliability:** Even with strong prompts, the agent may still fail to call tools correctly. This is a fundamental LLM limitation.

2. **RAGTool usage:** The agent must remember to call RAGTool for each section. May need prompt iteration.

3. **Context window:** With 8k context, very long articles may hit limits during revision.

---

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `prompts/research_task.yaml` | Template variable fixes | ~94 |
| `prompts/generation_task.yaml` | Template fixes + MANDATORY save instruction | ~108 |
| `prompts/audit_task.yaml` | No template issues | ~126 |
| `prompts/revision_task.yaml` | Template variable fixes | ~130 |
| `tools/scraper_tool.py` | Pydantic schema + field_validator | ~351 |
| `app/services/job_service.py` | Enhanced validation with fallbacks | ~179 |
| `agents/generator.py` | Model upgrade to llama3.1:8b | ~49 |

**Total:** 7 files modified
