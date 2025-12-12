# Proposed Architecture: Hierarchical Multi-Agent Content Factory

## Executive Summary

This document proposes an enhanced architecture for ANCA (Autonomous Niche Content Agent) based on first principles analysis and proven agentic design patterns. The new architecture addresses current limitations through parallel execution, early validation, specialized agents, and fact verification.

---

## Current Architecture Analysis

### Existing Pipeline

```
RESEARCHER → GENERATOR → CRITIQUE ⟲ → AUDITOR → REVISER ⟲ → END
```

### Identified Limitations

| Issue | Impact |
|-------|--------|
| **Sequential bottleneck** | Research is single-threaded, can't parallelize sources |
| **No upfront planning** | Generator writes without validated outline |
| **Late quality gates** | Critique happens after full 2000+ word draft |
| **Monolithic generator** | One agent writes all sections (intro, how-to, FAQ have different requirements) |
| **No fact verification** | Claims aren't validated against sources |
| **Tight coupling** | Fixed flow can't adapt to content type variations |
| **No learning loop** | System doesn't improve from past articles |

---

## First Principles for Article Writing

| Principle | Architectural Implication |
|-----------|---------------------------|
| **Planning precedes writing** | Outline validation before drafting |
| **Research depth = quality** | Parallel multi-source gathering |
| **Sections have specializations** | How-To ≠ FAQ ≠ Introduction |
| **Early failure is cheap** | Validate structure before 2000 words |
| **Iteration improves quality** | Multiple refinement passes |
| **Separation of concerns** | Writing ≠ Editing ≠ Fact-checking ≠ SEO |

---

## Proposed Architecture

### High-Level Overview

```
                                    ┌─────────────────────────────────────────┐
                                    │           ORCHESTRATOR                  │
                                    │   (Plan-and-Execute + Routing)          │
                                    └─────────────┬───────────────────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
                    ▼                             ▼                             ▼
        ┌───────────────────┐         ┌───────────────────┐         ┌───────────────────┐
        │   PHASE 1         │         │   PHASE 2         │         │   PHASE 3         │
        │   PLANNING        │         │   PRODUCTION      │         │   REFINEMENT      │
        └───────────────────┘         └───────────────────┘         └───────────────────┘
                    │                             │                             │
    ┌───────────────┼───────────────┐             │             ┌───────────────┼───────────────┐
    │               │               │             │             │               │               │
    ▼               ▼               ▼             ▼             ▼               ▼               ▼
┌───────┐     ┌───────────┐   ┌─────────┐   ┌─────────┐   ┌───────────┐   ┌─────────┐   ┌─────────┐
│Planner│     │ Research  │   │ Outline │   │ Section │   │   Fact    │   │   SEO   │   │  Style  │
│ Agent │────▶│   Swarm   │──▶│Validator│   │ Writers │   │  Checker  │   │ Auditor │   │ Editor  │
└───────┘     └───────────┘   └─────────┘   └─────────┘   └───────────┘   └─────────┘   └─────────┘
                    │                             │                             │
            ┌───────┴───────┐             ┌───────┴───────┐                     │
            │   PARALLEL    │             │   PARALLEL    │                     ▼
            ▼       ▼       ▼             ▼       ▼       ▼             ┌───────────────┐
         [R1]    [R2]    [R3]          [Intro] [Body] [FAQ]            │   ASSEMBLER   │
                                                                        │   + Publisher │
                                                                        └───────────────┘
```

---

## Layer 1: Orchestrator (Brain)

### Agent Specification

```yaml
Agent: ContentOrchestrator
Pattern: Plan-and-Execute + Routing
Role: Dynamic task decomposition and agent coordination

Capabilities:
  - Analyzes topic complexity to determine agent allocation
  - Creates execution plan with dependencies
  - Routes subtasks to specialized agents
  - Monitors progress and re-plans on failure
  - Maintains global article state

LLM: High-capability model (GPT-4, Claude, Llama 70B)
Temperature: 0.3 (consistent decision-making)
```

### Design Pattern Applied

**Orchestrator-Worker with Dynamic Planning**: Unlike the current fixed pipeline, the orchestrator adapts based on topic type (tutorial vs. listicle vs. deep-dive).

### Routing Logic

```python
def route_by_content_type(state: EnhancedAgentState) -> str:
    content_type = state["content_type"]

    routing_map = {
        "tutorial": "tutorial_pipeline",      # Step-by-step focus
        "listicle": "listicle_pipeline",      # Parallel item writers
        "deep_dive": "research_heavy_pipeline", # Extra research phase
        "comparison": "comparison_pipeline",   # Multi-subject research
    }

    return routing_map.get(content_type, "default_pipeline")
```

---

## Layer 2: Phase 1 - Planning Agents

### Agent Roster

| Agent | Pattern | Purpose |
|-------|---------|---------|
| **TopicAnalyzer** | ReAct | Analyzes topic, identifies content type, target audience, key angles |
| **ResearchSwarm** | Parallelization | 3-5 parallel researchers each targeting different source types |
| **OutlinePlanner** | Plan-and-Execute | Creates structured outline with section requirements |
| **OutlineValidator** | Reflection | Validates outline against SEO requirements, completeness |

### Research Swarm Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    RESEARCH SWARM                            │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ Academic   │  │ Industry   │  │ Tutorial   │  PARALLEL   │
│  │ Researcher │  │ Researcher │  │ Researcher │  EXECUTION  │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘             │
│        │               │               │                     │
│        └───────────────┼───────────────┘                     │
│                        ▼                                     │
│              ┌─────────────────┐                             │
│              │  Source Ranker  │  Deduplication + Scoring    │
│              │  & Synthesizer  │                             │
│              └─────────────────┘                             │
└──────────────────────────────────────────────────────────────┘
```

### Research Agent Specializations

```yaml
AcademicResearcher:
  search_domains: ["scholar.google.com", "arxiv.org", "pubmed.gov"]
  focus: "Peer-reviewed studies, statistics, citations"
  quality_criteria: "Publication date, citation count, journal reputation"

IndustryResearcher:
  search_domains: ["forbes.com", "hbr.org", "industry blogs"]
  focus: "Case studies, expert opinions, market data"
  quality_criteria: "Author credentials, company reputation, recency"

TutorialResearcher:
  search_domains: ["dev.to", "medium.com", "official docs"]
  focus: "How-to guides, code examples, best practices"
  quality_criteria: "Completeness, clarity, user engagement"
```

### Topic Analyzer Agent

```yaml
Agent: TopicAnalyzer
Pattern: ReAct
Purpose: Understand topic before research begins

Output Schema:
  content_type: enum[tutorial, listicle, deep_dive, comparison]
  target_audience: string
  primary_keyword: string
  secondary_keywords: list[string]
  search_intent: enum[informational, transactional, navigational]
  complexity_level: enum[beginner, intermediate, advanced]
  estimated_sections: list[string]
  research_queries: list[string]  # Seed queries for research swarm
```

### Outline Validator Agent

```yaml
Agent: OutlineValidator
Pattern: Reflection
Purpose: Quality gate before production phase

Validation Criteria:
  - Primary keyword in H1
  - Logical section flow
  - All required sections present (intro, body, FAQ, conclusion)
  - Word count targets per section are realistic
  - No duplicate content angles
  - Covers search intent comprehensively

Output:
  valid: boolean
  issues: list[ValidationIssue]
  suggestions: list[string]
```

---

## Layer 3: Phase 2 - Production Agents

### Agent Roster

| Agent | Pattern | Purpose |
|-------|---------|---------|
| **SectionWriters** | Parallelization + Specialization | Parallel writers for each major section |
| **IntroWriter** | Specialized | Hook-focused, value proposition, reader engagement |
| **BodyWriter** | Specialized | Depth, examples, step-by-step instructions |
| **FAQWriter** | Specialized | Concise Q&A format, common objections |
| **ConclusionWriter** | Specialized | Summary, CTA, next steps |

### Section Specifications

```python
SECTION_SPECS = {
    "introduction": {
        "word_target": 200,
        "requirements": ["hook", "value_proposition", "article_preview"],
        "tone": "engaging",
        "evaluator": IntroEvaluator,
        "prompt_template": "prompts/sections/introduction.yaml"
    },
    "what_is": {
        "word_target": 300,
        "requirements": ["definition", "context", "importance"],
        "tone": "educational",
        "evaluator": DefinitionEvaluator,
        "prompt_template": "prompts/sections/what_is.yaml"
    },
    "benefits": {
        "word_target": 300,
        "requirements": ["numbered_benefits", "examples", "evidence"],
        "tone": "persuasive",
        "evaluator": BenefitsEvaluator,
        "prompt_template": "prompts/sections/benefits.yaml"
    },
    "how_to": {
        "word_target": 800,
        "requirements": ["numbered_steps", "examples", "tips", "warnings"],
        "tone": "instructional",
        "evaluator": TutorialEvaluator,
        "prompt_template": "prompts/sections/how_to.yaml"
    },
    "common_mistakes": {
        "word_target": 300,
        "requirements": ["mistake_list", "solutions", "prevention"],
        "tone": "advisory",
        "evaluator": MistakesEvaluator,
        "prompt_template": "prompts/sections/mistakes.yaml"
    },
    "faq": {
        "word_target": 300,
        "requirements": ["5_questions", "concise_answers", "schema_markup"],
        "tone": "conversational",
        "evaluator": FAQEvaluator,
        "prompt_template": "prompts/sections/faq.yaml"
    },
    "conclusion": {
        "word_target": 150,
        "requirements": ["summary", "cta", "next_steps"],
        "tone": "motivational",
        "evaluator": ConclusionEvaluator,
        "prompt_template": "prompts/sections/conclusion.yaml"
    }
}
```

### Parallel Section Writing

```python
async def parallel_section_writers(state: EnhancedAgentState) -> EnhancedAgentState:
    """Execute section writers in parallel with fan-out/fan-in pattern."""

    outline = state["validated_outline"]
    research = state["research_sources"]

    # Create tasks for parallel execution
    tasks = []
    for section in outline.sections:
        spec = SECTION_SPECS[section.type]
        writer = SectionWriter(
            section_type=section.type,
            spec=spec,
            research_context=research,
            outline_guidance=section
        )
        tasks.append(writer.write())

    # Fan-out: Execute all writers in parallel
    section_drafts = await asyncio.gather(*tasks)

    # Fan-in: Collect results
    state["sections"] = {
        draft.section_type: draft
        for draft in section_drafts
    }

    return state
```

### Section Assembler

```yaml
Agent: SectionAssembler
Purpose: Combine sections into cohesive article

Responsibilities:
  - Order sections according to outline
  - Add transitions between sections
  - Ensure consistent formatting
  - Validate total word count
  - Generate table of contents if needed

Output: Complete first draft as single markdown document
```

---

## Layer 4: Phase 3 - Refinement Agents

### Refinement Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        REFINEMENT PIPELINE                                   │
│                                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│   │    Fact     │    │    SEO      │    │   Style     │    │  Coherence  │  │
│   │   Checker   │───▶│   Auditor   │───▶│   Editor    │───▶│   Reviewer  │  │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│          │                  │                  │                  │          │
│          ▼                  ▼                  ▼                  ▼          │
│   [Verify claims    [Keyword density   [Tone, clarity,    [Section flow,    │
│    against RAG]      H1/H2 structure]   readability]       transitions]     │
│                                                                              │
│                              ┌──────────────────┐                            │
│                              │   Quality Gate   │                            │
│                              │  (Score >= 9/10) │                            │
│                              └────────┬─────────┘                            │
│                                       │                                      │
│                    ┌──────────────────┼──────────────────┐                   │
│                    │ PASS             │ FAIL             │                   │
│                    ▼                  ▼                  │                   │
│             ┌──────────┐       ┌──────────────┐          │                   │
│             │ Publisher│       │ Targeted     │──────────┘                   │
│             │          │       │ Revision     │   (Loop back to              │
│             └──────────┘       └──────────────┘    failing stage)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fact Checker Agent (NEW)

```yaml
Agent: FactChecker
Pattern: ReAct + Reflection
Purpose: Verify claims against ingested sources
LLM: Analytical model with high accuracy

Process:
  1. Extract all factual claims from article
  2. For each claim:
     - Query RAG for supporting evidence
     - Score confidence (0-1)
     - Flag unsupported claims
  3. Generate verification report

Output Schema:
  claims: list[Claim]
  verified_count: int
  unverified_count: int
  confidence_score: float
  issues: list[FactIssue]
  suggested_citations: list[Citation]

Claim Schema:
  text: string
  location: string  # Section + paragraph
  sources: list[Source]
  confidence: float
  status: enum[verified, unverified, contradicted]
```

### SEO Auditor Agent

```yaml
Agent: SEOAuditor
Pattern: Evaluator
Purpose: SEO optimization scoring

Rubric (100 points):
  keyword_optimization: 25
    - H1 contains primary keyword (10)
    - H2s contain secondary keywords (5)
    - Keyword density 1-2% (5)
    - Keywords in first 100 words (5)

  structure: 25
    - Proper heading hierarchy (10)
    - Short paragraphs (<150 words) (5)
    - Bullet points for lists (5)
    - Internal linking opportunities (5)

  eeat_signals: 25
    - Author expertise demonstrated (10)
    - Data and statistics included (5)
    - External citations (5)
    - Original insights (5)

  technical: 25
    - Meta description quality (10)
    - Image alt text suggestions (5)
    - Schema markup opportunities (5)
    - Mobile readability (5)

Output:
  score: float  # 0-10
  breakdown: dict[category, score]
  issues: list[SEOIssue]
  quick_wins: list[string]  # Easy fixes
```

### Style Editor Agent

```yaml
Agent: StyleEditor
Pattern: Evaluator-Optimizer
Purpose: Readability and tone consistency

Checks:
  - Flesch-Kincaid readability score
  - Sentence length variation
  - Passive voice percentage
  - Jargon density
  - Tone consistency across sections
  - Transition quality

Fixes:
  - Simplify complex sentences
  - Convert passive to active voice
  - Add transitional phrases
  - Improve paragraph flow
```

### Coherence Reviewer Agent

```yaml
Agent: CoherenceReviewer
Pattern: Reflection
Purpose: Ensure article flows as unified piece

Checks:
  - Section transitions are smooth
  - No contradictions between sections
  - Consistent terminology throughout
  - Logical argument progression
  - Introduction promises match conclusion

Output:
  coherence_score: float
  transition_issues: list[TransitionIssue]
  contradiction_flags: list[Contradiction]
  terminology_inconsistencies: list[TermIssue]
```

### Targeted Revision Agent

```yaml
Agent: TargetedReviser
Pattern: Optimizer
Purpose: Fix specific issues without rewriting entire article

Input: List of issues from auditors
Process:
  1. Prioritize issues by severity (CRITICAL > HIGH > MEDIUM > LOW)
  2. For each issue:
     - Read relevant section
     - Apply minimal fix
     - Verify fix resolved issue
  3. Return patched article

Key Principle: Surgical edits, not rewrites
```

---

## Enhanced State Management

```python
from typing import TypedDict, List, Dict, Literal, Optional
from pydantic import BaseModel

class TopicAnalysis(BaseModel):
    content_type: Literal["tutorial", "listicle", "deep_dive", "comparison"]
    target_audience: str
    primary_keyword: str
    secondary_keywords: List[str]
    search_intent: Literal["informational", "transactional", "navigational"]
    complexity_level: Literal["beginner", "intermediate", "advanced"]

class ResearchSource(BaseModel):
    url: str
    title: str
    source_type: Literal["academic", "industry", "tutorial", "official"]
    quality_score: float
    key_facts: List[str]
    ingested: bool

class SectionDraft(BaseModel):
    section_type: str
    content: str
    word_count: int
    quality_score: float
    issues: List[str]

class ArticleOutline(BaseModel):
    title: str
    sections: List[SectionOutline]
    total_word_target: int
    validated: bool

class FactCheckReport(BaseModel):
    claims: List[Claim]
    verified_count: int
    unverified_count: int
    confidence_score: float

class EnhancedAgentState(TypedDict):
    # Core
    topic: str
    content_type: Literal["tutorial", "listicle", "deep_dive", "comparison"]

    # Planning Phase
    topic_analysis: Optional[TopicAnalysis]
    research_sources: List[ResearchSource]
    validated_outline: Optional[ArticleOutline]

    # Production Phase
    sections: Dict[str, SectionDraft]
    assembled_draft: Optional[str]

    # Refinement Phase
    fact_check_report: Optional[FactCheckReport]
    seo_audit: Optional[Dict]
    style_audit: Optional[Dict]
    coherence_audit: Optional[Dict]

    # Meta
    phase: Literal["planning", "production", "refinement", "complete"]
    iteration_counts: Dict[str, int]
    quality_score: float
    checkpoints: List[Dict]  # For human-in-the-loop

    # LangGraph
    messages: List[BaseMessage]
```

---

## LangGraph Implementation

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

def build_content_factory() -> CompiledGraph:
    """Build the hierarchical multi-agent content factory."""

    workflow = StateGraph(EnhancedAgentState)

    # ==================== PHASE 1: PLANNING ====================
    workflow.add_node("analyze_topic", topic_analyzer_node)
    workflow.add_node("research_swarm", parallel_research_node)
    workflow.add_node("synthesize_research", research_synthesizer_node)
    workflow.add_node("plan_outline", outline_planner_node)
    workflow.add_node("validate_outline", outline_validator_node)

    # ==================== PHASE 2: PRODUCTION ====================
    workflow.add_node("write_sections", parallel_section_writers_node)
    workflow.add_node("assemble_draft", section_assembler_node)

    # ==================== PHASE 3: REFINEMENT ====================
    workflow.add_node("fact_check", fact_checker_node)
    workflow.add_node("seo_audit", seo_auditor_node)
    workflow.add_node("style_edit", style_editor_node)
    workflow.add_node("coherence_review", coherence_reviewer_node)
    workflow.add_node("quality_gate", quality_gate_node)
    workflow.add_node("targeted_revision", targeted_reviser_node)
    workflow.add_node("publish", publisher_node)

    # ==================== EDGES ====================

    # Phase 1 flow
    workflow.add_edge("analyze_topic", "research_swarm")
    workflow.add_edge("research_swarm", "synthesize_research")
    workflow.add_edge("synthesize_research", "plan_outline")
    workflow.add_edge("plan_outline", "validate_outline")

    # Outline validation gate
    workflow.add_conditional_edges(
        "validate_outline",
        lambda s: "production" if s["validated_outline"].validated else "replan",
        {
            "production": "write_sections",
            "replan": "plan_outline"
        }
    )

    # Phase 2 flow
    workflow.add_edge("write_sections", "assemble_draft")
    workflow.add_edge("assemble_draft", "fact_check")

    # Phase 3 flow
    workflow.add_edge("fact_check", "seo_audit")
    workflow.add_edge("seo_audit", "style_edit")
    workflow.add_edge("style_edit", "coherence_review")
    workflow.add_edge("coherence_review", "quality_gate")

    # Quality gate
    workflow.add_conditional_edges(
        "quality_gate",
        quality_gate_router,
        {
            "pass": "publish",
            "revise": "targeted_revision",
            "fail": END  # Max iterations reached
        }
    )

    workflow.add_edge("targeted_revision", "quality_gate")
    workflow.add_edge("publish", END)

    # Entry point
    workflow.set_entry_point("analyze_topic")

    return workflow.compile()


def quality_gate_router(state: EnhancedAgentState) -> str:
    """Route based on quality score and iteration count."""
    score = state["quality_score"]
    iterations = state["iteration_counts"].get("refinement", 0)
    max_iterations = 3

    if score >= 9.0:
        return "pass"
    elif iterations >= max_iterations:
        return "fail"
    else:
        return "revise"
```

---

## Workflow Comparison

| Aspect | Current ANCA | Proposed Architecture |
|--------|--------------|----------------------|
| **Research** | Sequential, 1 agent | Parallel swarm, 3-5 agents |
| **Planning** | None (direct to writing) | Outline → Validation → Approval |
| **Writing** | Monolithic generator | Specialized section writers |
| **Quality Gates** | After full draft | Per-section + full article |
| **Fact Checking** | None | Dedicated FactChecker agent |
| **Iteration** | Fixed loops (3x) | Dynamic based on scores |
| **Adaptability** | Fixed pipeline | Orchestrator routes by content type |
| **Parallelization** | None | Research + Section writing |
| **State Tracking** | Basic | Rich typed state with checkpoints |

---

## Design Patterns Summary

| Pattern | Where Applied | Benefit |
|---------|--------------|---------|
| **Plan-and-Execute** | Orchestrator + Outline Planning | Validates structure before expensive generation |
| **Parallelization** | Research Swarm, Section Writers | 3-5x faster research and writing |
| **Reflection** | Outline Validator, Quality Gate | Self-correcting before human review |
| **Orchestrator-Worker** | Central coordinator + specialized agents | Dynamic routing based on content type |
| **Routing** | Content type → agent selection | Tutorials vs listicles get different treatment |
| **Evaluator-Optimizer** | Refinement pipeline | Iterative improvement until quality threshold |
| **ReAct** | Topic Analyzer, Fact Checker | Reasoning with tool use for complex analysis |

---

## Implementation Roadmap

### Phase 1: Enhanced Planning Layer (Week 1-2)

**Tasks:**
- [ ] Create TopicAnalyzer agent with content type detection
- [ ] Implement OutlinePlanner with section specifications
- [ ] Add OutlineValidator with quality criteria
- [ ] Create checkpoint system for outline approval
- [ ] Update state management with planning fields

**Files to Create:**
- `agents/topic_analyzer.py`
- `agents/outline_planner.py`
- `agents/outline_validator.py`
- `prompts/topic_analysis.yaml`
- `prompts/outline_planning.yaml`

### Phase 2: Parallel Research (Week 2-3)

**Tasks:**
- [ ] Refactor Researcher into ResearchSwarm
- [ ] Create specialized researcher prompts (academic, industry, tutorial)
- [ ] Implement source ranking and deduplication
- [ ] Add parallel execution with asyncio/LangGraph
- [ ] Create research synthesis step

**Files to Create:**
- `agents/research_swarm.py`
- `agents/source_synthesizer.py`
- `prompts/research/academic.yaml`
- `prompts/research/industry.yaml`
- `prompts/research/tutorial.yaml`

### Phase 3: Section Specialization (Week 3-4)

**Tasks:**
- [ ] Create specialized section writer prompts
- [ ] Implement parallel section generation
- [ ] Add per-section evaluation criteria
- [ ] Create SectionAssembler for draft compilation
- [ ] Add transition generation between sections

**Files to Create:**
- `agents/section_writers/intro_writer.py`
- `agents/section_writers/body_writer.py`
- `agents/section_writers/faq_writer.py`
- `agents/section_assembler.py`
- `prompts/sections/*.yaml`

### Phase 4: Refinement Pipeline (Week 4-5)

**Tasks:**
- [ ] Add FactChecker agent with RAG verification
- [ ] Separate SEO, Style, Coherence auditors
- [ ] Implement targeted revision (surgical fixes)
- [ ] Create quality gate with dynamic routing
- [ ] Add publisher with final validation

**Files to Create:**
- `agents/fact_checker.py`
- `agents/style_editor.py`
- `agents/coherence_reviewer.py`
- `agents/targeted_reviser.py`
- `prompts/refinement/*.yaml`

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Research time | ~5 min | ~2 min (parallel) |
| Draft generation | ~10 min | ~5 min (parallel sections) |
| First-pass quality | ~7/10 | ~8/10 (better planning) |
| Fact accuracy | Unknown | >95% verified claims |
| Revision iterations | 2-3 fixed | 1-2 (targeted fixes) |
| Total pipeline time | ~30 min | ~15 min |

---

## References

### Agentic Design Patterns
- [Building Effective Agents - Anthropic](https://www.anthropic.com/engineering/building-effective-agents)
- [LangGraph Multi-Agent Workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/)
- [Agentic AI Design Patterns - Microsoft Azure](https://azure.microsoft.com/en-us/blog/agent-factory-the-new-era-of-agentic-ai-common-use-cases-and-design-patterns/)

### Research Papers
- [A Survey on Large Language Model based Autonomous Agents](https://arxiv.org/pdf/2308.11432)
- [LLM-Based Multi-Agent Systems for Software Engineering](https://dl.acm.org/doi/10.1145/3712003)

### Frameworks
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [CrewAI Documentation](https://docs.crewai.com/)
