"""
SEO Auditor Agent
Evaluates content quality and provides feedback for revisions
"""
from crewai import Agent, LLM
from typing import List
from crewai.tools import BaseTool


def create_auditor(tools: List[BaseTool], base_url: str = "http://localhost:11434") -> Agent:
    """
    Create the SEO Auditor agent with critique model.
    Uses mistral:7b for better analysis and feedback.

    Args:
        tools: List of tools available to the agent
        base_url: Ollama base URL

    Returns:
        Configured SEO Auditor agent
    """
    import logging
    logger = logging.getLogger(__name__)

    model_name = "ollama/mistral:7b"
    logger.info(f"Creating Auditor agent with model: {model_name} at {base_url}")

    llm = LLM(
        model=model_name,
        base_url=base_url,
        temperature=0.3  # Lower temp for consistent critique
    )

    return Agent(
        role='SEO Auditor',
        goal='Evaluate blog posts for SEO quality, E-E-A-T compliance, and provide actionable feedback for improvement.',
        backstory=(
            "You are an expert SEO consultant and content quality analyst. "
            "You have years of experience evaluating content for Google's E-E-A-T guidelines "
            "(Experience, Expertise, Authoritativeness, Trustworthiness). "
            "You provide clear, actionable feedback to improve content quality and search rankings."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools
    )
