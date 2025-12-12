"""
Enhanced State Management for ANCA v2

This module defines the state schema for the v2 hierarchical multi-agent architecture.
Uses Pydantic for strong typing and validation.
"""

from typing import List, Dict, Optional, Literal, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# ============================================================================
# Planning Phase Models
# ============================================================================

class TopicAnalysis(BaseModel):
    """Analysis of the content topic to guide agent behavior."""

    content_type: Literal["tutorial", "listicle", "deep_dive", "comparison"] = Field(
        description="Type of content to generate"
    )
    target_audience: str = Field(
        description="Primary audience for this content"
    )
    primary_keyword: str = Field(
        description="Main SEO keyword to target"
    )
    secondary_keywords: List[str] = Field(
        default_factory=list,
        description="Supporting keywords for SEO"
    )
    search_intent: Literal["informational", "transactional", "navigational"] = Field(
        description="User's search intent"
    )
    complexity_level: Literal["beginner", "intermediate", "advanced"] = Field(
        description="Content complexity level"
    )
    estimated_sections: List[str] = Field(
        default_factory=list,
        description="Predicted section names"
    )
    research_queries: List[str] = Field(
        default_factory=list,
        description="Seed queries for research agents"
    )


class ResearchSource(BaseModel):
    """A single research source with metadata and extracted facts."""

    url: str = Field(description="Source URL")
    title: str = Field(default="", description="Page title")
    source_type: Literal["academic", "industry", "tutorial", "official", "other"] = Field(
        description="Type of source"
    )
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Quality score (0-1)"
    )
    key_facts: List[str] = Field(
        default_factory=list,
        description="Key facts extracted from source"
    )
    ingested: bool = Field(
        default=False,
        description="Whether source has been ingested into RAG"
    )
    word_count: int = Field(
        default=0,
        description="Approximate word count of source"
    )


class SectionOutline(BaseModel):
    """Outline for a single section of the article."""

    section_type: str = Field(description="Type of section (intro, body, faq, etc.)")
    heading: str = Field(description="Section heading/title")
    word_target: int = Field(description="Target word count")
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points to cover"
    )
    requirements: List[str] = Field(
        default_factory=list,
        description="Specific requirements for this section"
    )


class ArticleOutline(BaseModel):
    """Complete outline for the article."""

    title: str = Field(description="Article H1 title")
    sections: List[SectionOutline] = Field(
        default_factory=list,
        description="Ordered list of sections"
    )
    total_word_target: int = Field(
        default=1800,
        description="Total target word count"
    )
    validated: bool = Field(
        default=False,
        description="Whether outline has passed validation"
    )
    validation_issues: List[str] = Field(
        default_factory=list,
        description="Issues found during validation"
    )


# ============================================================================
# Production Phase Models
# ============================================================================

class SectionDraft(BaseModel):
    """Draft content for a single section."""

    section_type: str = Field(description="Type of section")
    heading: str = Field(description="Section heading")
    content: str = Field(description="Markdown content")
    word_count: int = Field(description="Actual word count")
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="Self-assessed quality (0-10)"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Known issues with this section"
    )
    citations: List[str] = Field(
        default_factory=list,
        description="URLs cited in this section"
    )


# ============================================================================
# Refinement Phase Models
# ============================================================================

class Claim(BaseModel):
    """A factual claim that needs verification."""

    text: str = Field(description="The claim text")
    location: str = Field(description="Section and paragraph location")
    sources: List[str] = Field(
        default_factory=list,
        description="Supporting source URLs"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in verification (0-1)"
    )
    status: Literal["verified", "unverified", "contradicted"] = Field(
        description="Verification status"
    )


class FactCheckReport(BaseModel):
    """Results of fact-checking the article."""

    claims: List[Claim] = Field(
        default_factory=list,
        description="All extracted claims"
    )
    verified_count: int = Field(default=0)
    unverified_count: int = Field(default=0)
    contradicted_count: int = Field(default=0)
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence (0-1)"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Fact-checking issues found"
    )


class SEOAudit(BaseModel):
    """SEO audit results."""

    score: float = Field(
        ge=0.0,
        le=10.0,
        description="Overall SEO score (0-10)"
    )
    keyword_optimization: float = Field(default=0.0)
    structure: float = Field(default=0.0)
    eeat_signals: float = Field(default=0.0)
    technical: float = Field(default=0.0)
    issues: List[str] = Field(default_factory=list)
    quick_wins: List[str] = Field(
        default_factory=list,
        description="Easy fixes for immediate improvement"
    )


class StyleAudit(BaseModel):
    """Style and readability audit results."""

    readability_score: float = Field(
        default=0.0,
        description="Flesch-Kincaid or similar score"
    )
    avg_sentence_length: float = Field(default=0.0)
    passive_voice_percentage: float = Field(default=0.0)
    tone_consistency: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0
    )
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class CoherenceAudit(BaseModel):
    """Coherence and flow audit results."""

    coherence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0
    )
    transition_quality: float = Field(default=0.0)
    contradictions: List[str] = Field(
        default_factory=list,
        description="Contradictions found between sections"
    )
    terminology_inconsistencies: List[str] = Field(
        default_factory=list
    )
    flow_issues: List[str] = Field(default_factory=list)


class Issue(BaseModel):
    """A specific issue found during refinement."""

    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = Field(
        description="Issue severity"
    )
    category: str = Field(description="Issue category (seo, style, facts, etc.)")
    description: str = Field(description="What the issue is")
    location: str = Field(description="Where the issue is (section/paragraph)")
    suggested_fix: Optional[str] = Field(
        default=None,
        description="Suggested fix"
    )


# ============================================================================
# Checkpoints (for human-in-the-loop)
# ============================================================================

class Checkpoint(BaseModel):
    """A checkpoint where human review can occur."""

    checkpoint_type: Literal["outline_approval", "draft_review", "final_approval"]
    timestamp: str
    approved: Optional[bool] = None
    feedback: Optional[str] = None


# ============================================================================
# Main State TypedDict
# ============================================================================

class EnhancedAgentState(TypedDict):
    """
    Enhanced state for ANCA v2 multi-agent system.

    This state flows through all agents in the graph and is updated at each step.
    """

    # ========== Core ==========
    topic: str  # The content topic
    content_type: Optional[Literal["tutorial", "listicle", "deep_dive", "comparison"]]

    # ========== Planning Phase ==========
    topic_analysis: Optional[TopicAnalysis]
    research_sources: List[ResearchSource]  # Structured sources, not just URLs
    validated_outline: Optional[ArticleOutline]

    # ========== Production Phase ==========
    sections: Dict[str, SectionDraft]  # Per-section drafts
    assembled_draft: Optional[str]  # Complete article markdown

    # ========== Refinement Phase ==========
    fact_check_report: Optional[FactCheckReport]
    seo_audit: Optional[SEOAudit]
    style_audit: Optional[StyleAudit]
    coherence_audit: Optional[CoherenceAudit]
    all_issues: List[Issue]  # Aggregated issues from all audits

    # ========== Meta ==========
    phase: Literal["planning", "production", "refinement", "complete"]
    iteration_counts: Dict[str, int]  # Track iterations per phase
    quality_score: float  # Overall quality (0-10)
    checkpoints: List[Checkpoint]  # For human-in-the-loop

    # ========== LangGraph Message History ==========
    messages: Annotated[List[BaseMessage], add_messages]

    # ========== File Management ==========
    filename: Optional[str]  # Generated filename for article
    target_length: int  # Minimum word count target


# ============================================================================
# Helper Functions
# ============================================================================

def create_initial_state(topic: str, target_length: int = 1800) -> EnhancedAgentState:
    """Create initial state for a new content generation run."""
    import re

    # Generate filename from topic
    slug = topic.lower().replace(' ', '-').replace('_', '-')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    filename = f"{slug}.md"

    return EnhancedAgentState(
        topic=topic,
        content_type=None,
        topic_analysis=None,
        research_sources=[],
        validated_outline=None,
        sections={},
        assembled_draft=None,
        fact_check_report=None,
        seo_audit=None,
        style_audit=None,
        coherence_audit=None,
        all_issues=[],
        phase="planning",
        iteration_counts={},
        quality_score=0.0,
        checkpoints=[],
        messages=[],
        filename=filename,
        target_length=target_length,
    )


def aggregate_quality_score(state: EnhancedAgentState) -> float:
    """
    Calculate overall quality score from all audits.

    Weighted average:
    - Fact check: 30%
    - SEO: 30%
    - Style: 20%
    - Coherence: 20%
    """
    scores = []
    weights = []

    if state.get("fact_check_report"):
        scores.append(state["fact_check_report"].confidence_score * 10)
        weights.append(0.30)

    if state.get("seo_audit"):
        scores.append(state["seo_audit"].score)
        weights.append(0.30)

    if state.get("style_audit"):
        # Normalize readability to 0-10 scale (assuming Flesch-Kincaid)
        # 60+ is good (map to 8+), 50-60 is OK (map to 6-8)
        readability = state["style_audit"].readability_score
        normalized = min(10, max(0, (readability / 10)))
        scores.append(normalized)
        weights.append(0.20)

    if state.get("coherence_audit"):
        scores.append(state["coherence_audit"].coherence_score)
        weights.append(0.20)

    if not scores:
        return 0.0

    # Weighted average
    total_weight = sum(weights)
    weighted_sum = sum(s * w for s, w in zip(scores, weights))

    return weighted_sum / total_weight if total_weight > 0 else 0.0
