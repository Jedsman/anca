# ANCA v2 Migration Plan

## Overview

This document outlines the step-by-step migration from ANCA v1 (linear pipeline) to ANCA v2 (hierarchical multi-agent architecture). The migration follows an incremental approach, preserving working infrastructure while rebuilding the agent layer.

---

## Branch Strategy

```
main (current)
  └── v2-multiagent (new branch)
        ├── Phase 1: Scaffold
        ├── Phase 2: Planning Layer
        ├── Phase 3: Production Layer
        ├── Phase 4: Refinement Layer
        └── Phase 5: Integration
```

---

## What We Keep (No Changes)

These components are production-ready and will be imported as-is:

| Component | Path | Reason |
|-----------|------|--------|
| Scraper Tool | `tools/scraper_tool.py` | Caching, robots.txt, chunking all working |
| RAG Tool | `tools/rag_tool.py` | ChromaDB integration solid |
| Search Tool | `tools/search_tool.py` | DuckDuckGo wrapper works |
| File Tools | `tools/file_*.py` | Read/write articles |
| Word Count | `tools/word_count_tool.py` | Markdown-aware counting |
| Rate Limiter | `app/core/rate_limiter.py` | Token bucket for API limits |
| Logging | `app/core/logging_*.py` | Session logs, callbacks |
| Config | `app/core/config.py` | Settings management |
| API Layer | `app/api/` | FastAPI routes (update later) |

---

## New Directory Structure

```
anca/
├── tools/                    # KEEP - no changes
├── app/
│   ├── core/                 # KEEP - no changes
│   └── api/                  # UPDATE - add v2 endpoints later
├── prompts/
│   ├── v1/                   # MOVE existing prompts here
│   └── v2/                   # NEW - v2 prompts
│       ├── planning/
│       │   ├── topic_analysis.yaml
│       │   ├── research_academic.yaml
│       │   ├── research_industry.yaml
│       │   ├── research_tutorial.yaml
│       │   ├── outline_planning.yaml
│       │   └── outline_validation.yaml
│       ├── production/
│       │   ├── section_intro.yaml
│       │   ├── section_body.yaml
│       │   ├── section_faq.yaml
│       │   ├── section_conclusion.yaml
│       │   └── assembly.yaml
│       └── refinement/
│           ├── fact_checking.yaml
│           ├── seo_audit.yaml
│           ├── style_editing.yaml
│           └── coherence_review.yaml
├── agents_v2/                # NEW - v2 agent architecture
│   ├── __init__.py
│   ├── state.py              # Enhanced typed state
│   ├── orchestrator.py       # Central coordinator
│   ├── planning/
│   │   ├── __init__.py
│   │   ├── topic_analyzer.py
│   │   ├── research_swarm.py
│   │   ├── source_synthesizer.py
│   │   ├── outline_planner.py
│   │   └── outline_validator.py
│   ├── production/
│   │   ├── __init__.py
│   │   ├── section_writer.py   # Base class
│   │   ├── intro_writer.py
│   │   ├── body_writer.py
│   │   ├── faq_writer.py
│   │   ├── conclusion_writer.py
│   │   └── assembler.py
│   └── refinement/
│       ├── __init__.py
│       ├── fact_checker.py
│       ├── seo_auditor.py
│       ├── style_editor.py
│       ├── coherence_reviewer.py
│       ├── quality_gate.py
│       └── targeted_reviser.py
├── graph_v2.py               # NEW - LangGraph with parallel branches
├── run_graph.py              # KEEP - v1 for comparison
└── run_graph_v2.py           # NEW - v2 entry point
```

---

## Phase 1: Scaffold & State (Day 1)

### Objectives
- Create branch and directory structure
- Define enhanced state schema
- Set up base classes

### Tasks

- [ ] **1.1** Create branch `v2-multiagent`
  ```bash
  git checkout -b v2-multiagent
  ```

- [ ] **1.2** Create directory structure
  ```bash
  mkdir -p agents_v2/{planning,production,refinement}
  mkdir -p prompts/v2/{planning,production,refinement}
  touch agents_v2/__init__.py
  touch agents_v2/planning/__init__.py
  touch agents_v2/production/__init__.py
  touch agents_v2/refinement/__init__.py
  ```

- [ ] **1.3** Create `agents_v2/state.py` with enhanced state schema
  ```python
  # Key additions:
  # - TopicAnalysis (content_type, audience, keywords)
  # - ResearchSource (url, type, quality_score, key_facts)
  # - ArticleOutline (sections with word targets)
  # - SectionDraft (per-section content + scores)
  # - FactCheckReport, SEOAudit, StyleAudit
  # - Phase tracking, iteration counts, checkpoints
  ```

- [ ] **1.4** Create `agents_v2/base.py` with base agent class
  ```python
  # Shared functionality:
  # - Prompt loading from YAML
  # - LLM configuration (model selection, rate limiting)
  # - Logging callbacks
  # - Tool binding helpers
  ```

- [ ] **1.5** Create skeleton `graph_v2.py`
  ```python
  # Empty graph structure with:
  # - StateGraph(EnhancedAgentState)
  # - Placeholder nodes for each agent
  # - Conditional edges defined but not implemented
  ```

### Deliverables
- [ ] Branch created
- [ ] Directory structure in place
- [ ] `state.py` with all Pydantic models
- [ ] `base.py` with shared utilities
- [ ] Skeleton graph compiles (empty nodes)

---

## Phase 2: Planning Layer (Days 2-3)

### Objectives
- Build topic analysis
- Implement parallel research swarm
- Create outline planning + validation

### Tasks

- [ ] **2.1** Create `prompts/v2/planning/topic_analysis.yaml`
  - Content type detection (tutorial, listicle, deep_dive, comparison)
  - Audience identification
  - Keyword extraction
  - Search query generation

- [ ] **2.2** Implement `agents_v2/planning/topic_analyzer.py`
  - ReAct pattern with web_search tool
  - Output: TopicAnalysis model
  - Uses Groq for speed

- [ ] **2.3** Create research prompts (3 variants)
  - `research_academic.yaml` - scholarly sources
  - `research_industry.yaml` - business/expert sources
  - `research_tutorial.yaml` - how-to/practical sources

- [ ] **2.4** Implement `agents_v2/planning/research_swarm.py`
  - Parallel execution of 3 researcher agents
  - Each uses scrape_website + ingest_content
  - Fan-out/fan-in pattern with asyncio

- [ ] **2.5** Implement `agents_v2/planning/source_synthesizer.py`
  - Deduplicate sources
  - Rank by quality score
  - Extract key facts for outline

- [ ] **2.6** Create `prompts/v2/planning/outline_planning.yaml`
  - Section structure template
  - Word count targets per section
  - SEO requirements

- [ ] **2.7** Implement `agents_v2/planning/outline_planner.py`
  - Uses retrieve_context from RAG
  - Outputs ArticleOutline model

- [ ] **2.8** Create `prompts/v2/planning/outline_validation.yaml`
  - Completeness criteria
  - SEO checklist
  - Logical flow validation

- [ ] **2.9** Implement `agents_v2/planning/outline_validator.py`
  - Reflection pattern (self-evaluation)
  - Returns validation result + issues

- [ ] **2.10** Wire planning nodes into `graph_v2.py`
  ```python
  workflow.add_node("analyze_topic", topic_analyzer_node)
  workflow.add_node("research_swarm", parallel_research_node)
  workflow.add_node("synthesize_sources", source_synthesizer_node)
  workflow.add_node("plan_outline", outline_planner_node)
  workflow.add_node("validate_outline", outline_validator_node)
  ```

- [ ] **2.11** Add conditional edge for outline validation
  - VALID -> proceed to production
  - INVALID -> replan (max 2 attempts)

### Deliverables
- [ ] Topic analyzer working standalone
- [ ] Research swarm produces 5+ sources in parallel
- [ ] Outline planner creates structured outline
- [ ] Outline validator gates bad outlines
- [ ] Planning subgraph runs end-to-end

### Test Command
```bash
python -c "from graph_v2 import build_planning_subgraph; g = build_planning_subgraph(); print(g.invoke({'topic': 'how to brew coffee'}))"
```

---

## Phase 3: Production Layer (Days 4-5)

### Objectives
- Build specialized section writers
- Implement parallel section generation
- Create section assembler

### Tasks

- [ ] **3.1** Create `agents_v2/production/section_writer.py` (base class)
  ```python
  class SectionWriter:
      def __init__(self, section_type: str, spec: SectionSpec):
          self.section_type = section_type
          self.word_target = spec.word_target
          self.requirements = spec.requirements
          self.prompt = load_prompt(f"production/section_{section_type}.yaml")

      async def write(self, outline: ArticleOutline, research: List[ResearchSource]) -> SectionDraft:
          # Retrieve relevant context
          # Generate section
          # Validate against requirements
          # Return SectionDraft
  ```

- [ ] **3.2** Create section prompts
  - `section_intro.yaml` - hook, value prop, preview
  - `section_what_is.yaml` - definition, context
  - `section_benefits.yaml` - numbered benefits with evidence
  - `section_how_to.yaml` - step-by-step instructions
  - `section_mistakes.yaml` - common errors + solutions
  - `section_faq.yaml` - Q&A format
  - `section_conclusion.yaml` - summary, CTA

- [ ] **3.3** Implement specialized writers (inherit from base)
  - `intro_writer.py`
  - `body_writer.py` (handles what_is, benefits, how_to, mistakes)
  - `faq_writer.py`
  - `conclusion_writer.py`

- [ ] **3.4** Implement parallel section generation
  ```python
  async def parallel_section_writers_node(state):
      writers = [
          IntroWriter(state["validated_outline"]),
          BodyWriter(state["validated_outline"]),
          FAQWriter(state["validated_outline"]),
          ConclusionWriter(state["validated_outline"]),
      ]
      sections = await asyncio.gather(*[w.write() for w in writers])
      return {"sections": {s.section_type: s for s in sections}}
  ```

- [ ] **3.5** Create `prompts/v2/production/assembly.yaml`
  - Section ordering rules
  - Transition templates
  - Formatting standards

- [ ] **3.6** Implement `agents_v2/production/assembler.py`
  - Combines sections in order
  - Generates transitions between sections
  - Validates total word count
  - Outputs complete markdown draft

- [ ] **3.7** Wire production nodes into `graph_v2.py`
  ```python
  workflow.add_node("write_sections", parallel_section_writers_node)
  workflow.add_node("assemble_draft", assembler_node)
  ```

### Deliverables
- [ ] Each section writer works standalone
- [ ] Parallel generation completes faster than sequential
- [ ] Assembler produces cohesive draft
- [ ] Production subgraph runs end-to-end

### Test Command
```bash
python -c "from graph_v2 import build_production_subgraph; ..."
```

---

## Phase 4: Refinement Layer (Days 6-7)

### Objectives
- Build fact checker with RAG verification
- Implement SEO, style, coherence auditors
- Create quality gate and targeted reviser

### Tasks

- [ ] **4.1** Create `prompts/v2/refinement/fact_checking.yaml`
  - Claim extraction rules
  - Verification criteria
  - Citation format

- [ ] **4.2** Implement `agents_v2/refinement/fact_checker.py`
  - Extract factual claims from article
  - Query RAG for each claim
  - Score confidence (0-1)
  - Flag unsupported claims
  - Output: FactCheckReport

- [ ] **4.3** Create `prompts/v2/refinement/seo_audit.yaml`
  - 100-point rubric (keyword, structure, E-E-A-T, technical)
  - Issue severity levels
  - Quick win identification

- [ ] **4.4** Implement `agents_v2/refinement/seo_auditor.py`
  - Mirrors v1 auditor logic
  - Enhanced rubric scoring
  - Output: SEOAudit with breakdown

- [ ] **4.5** Create `prompts/v2/refinement/style_editing.yaml`
  - Readability metrics
  - Tone consistency rules
  - Paragraph/sentence guidelines

- [ ] **4.6** Implement `agents_v2/refinement/style_editor.py`
  - Flesch-Kincaid scoring
  - Passive voice detection
  - Transition quality check
  - Output: StyleAudit

- [ ] **4.7** Create `prompts/v2/refinement/coherence_review.yaml`
  - Section flow validation
  - Contradiction detection
  - Terminology consistency

- [ ] **4.8** Implement `agents_v2/refinement/coherence_reviewer.py`
  - Cross-section analysis
  - Output: CoherenceAudit

- [ ] **4.9** Implement `agents_v2/refinement/quality_gate.py`
  - Aggregates all audit scores
  - Calculates overall quality score
  - Routes: PASS (>=9), REVISE (<9), FAIL (max iterations)

- [ ] **4.10** Implement `agents_v2/refinement/targeted_reviser.py`
  - Takes list of issues from audits
  - Prioritizes by severity
  - Makes surgical fixes (not full rewrite)
  - Preserves working sections

- [ ] **4.11** Wire refinement nodes into `graph_v2.py`
  ```python
  workflow.add_node("fact_check", fact_checker_node)
  workflow.add_node("seo_audit", seo_auditor_node)
  workflow.add_node("style_edit", style_editor_node)
  workflow.add_node("coherence_review", coherence_reviewer_node)
  workflow.add_node("quality_gate", quality_gate_node)
  workflow.add_node("targeted_revision", targeted_reviser_node)
  ```

- [ ] **4.12** Add conditional edges for quality loop
  ```python
  workflow.add_conditional_edges(
      "quality_gate",
      quality_gate_router,
      {"pass": "publish", "revise": "targeted_revision", "fail": END}
  )
  workflow.add_edge("targeted_revision", "quality_gate")
  ```

### Deliverables
- [ ] Fact checker identifies unsupported claims
- [ ] All auditors produce structured reports
- [ ] Quality gate routes correctly
- [ ] Targeted reviser fixes specific issues
- [ ] Refinement subgraph runs end-to-end

---

## Phase 5: Integration & Testing (Days 8-9)

### Objectives
- Connect all layers
- End-to-end testing
- Performance comparison with v1

### Tasks

- [ ] **5.1** Complete `graph_v2.py` with all edges
  ```python
  # Planning -> Production
  workflow.add_edge("validate_outline", "write_sections")

  # Production -> Refinement
  workflow.add_edge("assemble_draft", "fact_check")
  ```

- [ ] **5.2** Create `run_graph_v2.py` entry point
  - CLI argument parsing
  - Logging setup
  - Graph invocation
  - Result validation

- [ ] **5.3** Test with sample topics
  - Tutorial: "how to brew coffee at home"
  - Listicle: "10 best productivity apps"
  - Deep dive: "understanding machine learning"
  - Comparison: "react vs vue vs angular"

- [ ] **5.4** Performance benchmarks
  | Metric | v1 | v2 Target |
  |--------|----|-----------|
  | Research time | 5 min | 2 min |
  | Generation time | 10 min | 5 min |
  | Total pipeline | 30 min | 15 min |
  | Quality score | 7/10 | 8.5/10 |

- [ ] **5.5** Fix bugs and edge cases

- [ ] **5.6** Update API layer (`app/api/routers/generation.py`)
  - Add `/v2/generate` endpoint
  - Keep v1 endpoint for comparison

- [ ] **5.7** Documentation
  - Update README with v2 usage
  - Add architecture diagram
  - Document new prompts

### Deliverables
- [ ] Full pipeline runs without errors
- [ ] Performance meets targets
- [ ] API endpoints working
- [ ] Documentation complete

---

## Phase 6: Optimization (Day 10+)

### Optional Enhancements

- [ ] **6.1** Add human-in-the-loop checkpoints
  - Outline approval before writing
  - Draft review before refinement

- [ ] **6.2** Implement caching layer
  - Cache topic analysis for similar topics
  - Cache research for repeated runs

- [ ] **6.3** Add streaming output
  - Stream sections as they complete
  - Real-time progress updates

- [ ] **6.4** Model experimentation
  - Test different models per agent
  - Optimize cost/quality tradeoffs

- [ ] **6.5** Learning loop
  - Store successful articles
  - Use as few-shot examples for future runs

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Parallel execution complexity | Start with sequential, add parallel later |
| LLM rate limits | Existing rate limiter handles this |
| State management bugs | Strong typing with Pydantic |
| Regression in quality | Keep v1 for A/B comparison |
| Scope creep | Strict phase boundaries |

---

## Success Criteria

### Minimum Viable v2
- [ ] Planning layer produces validated outlines
- [ ] Production layer generates all sections
- [ ] Refinement layer scores >= 8/10
- [ ] End-to-end pipeline completes

### Full Success
- [ ] 50% faster than v1
- [ ] Higher quality scores (8.5+ vs 7)
- [ ] Fact verification working
- [ ] Parallel execution active

---

## Commands Reference

```bash
# Create branch
git checkout -b v2-multiagent

# Run v1 (baseline)
python run_graph.py --topic "how to brew coffee"

# Run v2 (new architecture)
python run_graph_v2.py --topic "how to brew coffee"

# Test individual subgraphs
python -m pytest tests/test_planning_v2.py
python -m pytest tests/test_production_v2.py
python -m pytest tests/test_refinement_v2.py

# Compare outputs
diff articles/v1/coffee.md articles/v2/coffee.md
```

---

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|-----------------|
| 1. Scaffold | 1 day | State + structure |
| 2. Planning | 2 days | Research swarm + outline |
| 3. Production | 2 days | Parallel section writers |
| 4. Refinement | 2 days | Fact checker + quality gate |
| 5. Integration | 2 days | End-to-end pipeline |
| 6. Optimization | Ongoing | Performance tuning |

**Total: ~9-10 days to MVP**
