"""
Content Generator Agent
Writes comprehensive, SEO-optimized blog posts based on research and source material.
"""
from crewai import Agent, LLM
from typing import List
from crewai.tools import BaseTool


def create_generator(tools: List[BaseTool], base_url: str = "http://localhost:11434") -> Agent:
    """
    Create the Content Generator agent with optimized writing model.
    Uses qwen2.5:3b for quality content generation.

    Args:
        tools: List of tools available to the agent
        base_url: Ollama base URL

    Returns:
        Configured Content Generator agent
    """
    import logging
    logger = logging.getLogger(__name__)

    model_name = "ollama/qwen2.5:3b"
    logger.info(f"Creating Generator agent with model: {model_name} at {base_url}")

    llm = LLM(
        model=model_name,
        base_url=base_url,
        temperature=0.7  # Higher temp for creative writing
    )

    return Agent(
        role='Content Generator',
        goal='Create and revise comprehensive, SEO-optimized blog posts using multiple sources, RAG for context retrieval, and incorporating feedback.',
        backstory=(
            "You are a talented content creator and editor. You excel at synthesizing "
            "information from multiple sources into original, engaging articles. "
            "You use RAG (Retrieval-Augmented Generation) to access relevant context "
            "and are skilled at incorporating editorial feedback to improve your work. "
            "You write clear, well-structured content ready for publication."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
        tools=tools
    )
