"""
Market Researcher Agent
Identifies low-competition, high-intent long-tail keywords for content creation.
"""
from crewai import Agent, LLM
from typing import List
from crewai.tools import BaseTool


def create_researcher(tools: List[BaseTool], base_url: str = "http://localhost:11434") -> Agent:
    """
    Create the Market Researcher agent with optimized small model.
    Uses llama3.2:3b for fast keyword research.

    Args:
        tools: List of tools available to the agent
        base_url: Ollama base URL

    Returns:
        Configured Market Researcher agent
    """
    import logging
    logger = logging.getLogger(__name__)

    model_name = "ollama/llama3.2:3b"
    logger.info(f"Creating Researcher agent with model: {model_name} at {base_url}")

    llm = LLM(
        model=model_name,
        base_url=base_url,
        temperature=0.5  # Lower temp for more focused research
    )

    return Agent(
        role='Market Researcher',
        goal='Find 3-5 high-quality, diverse sources from different domains for a given topic, along with a promising long-tail keyword for SEO.',
        backstory=(
            "You are an expert SEO analyst and content researcher. "
            "You excel at identifying untapped niches and finding diverse, "
            "authoritative sources from different domains. You understand that "
            "quality content requires multiple perspectives and credible sources."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools
    )
