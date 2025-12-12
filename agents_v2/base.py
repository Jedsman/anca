"""
Base Agent Class and Shared Utilities for ANCA v2

This module provides common functionality for all agents in the v2 architecture.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from app.core.langchain_logging_callback import LangChainLoggingHandler
from app.core.rate_limiter import groq_rate_limiter, gemini_rate_limiter


logger = logging.getLogger(__name__)


# ============================================================================
# Prompt Loading
# ============================================================================

def load_prompt(filename: str, version: str = "v2") -> dict:
    """
    Load a YAML prompt file from the prompts directory.

    Args:
        filename: Name of the prompt file (e.g., 'planning/topic_analysis.yaml')
        version: Version directory ('v1' or 'v2')

    Returns:
        Dictionary with prompt configuration

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompts_dir = Path(__file__).parent.parent / "prompts" / version
    file_path = prompts_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================================
# Rate-Limited LLM Wrappers
# ============================================================================

class RateLimitedGroq(ChatGroq):
    """Groq wrapper with token bucket rate limiting."""

    def _generate(self, *args, **kwargs):
        logger.debug("[GROQ] Acquiring rate limit token")
        groq_rate_limiter.acquire()
        try:
            return super()._generate(*args, **kwargs)
        except Exception as e:
            logger.error(f"[GROQ] Generation error: {e}")
            raise


class RateLimitedGemini:
    """
    Placeholder for Gemini rate limiting.
    Implement if using Gemini models in the future.
    """
    pass


# ============================================================================
# LLM Configuration Factory
# ============================================================================

class LLMConfig:
    """Configuration for different LLM models used in the system."""

    # Model specifications
    MODELS = {
        "groq_fast": {
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
            "context": 128000,
            "use_cases": ["research", "generation", "planning"],
        },
        "ollama_local": {
            "provider": "ollama",
            "model": "qwen2.5:7b",
            "context": 32000,
            "use_cases": ["audit", "critique", "revision"],
        },
    }

    @staticmethod
    def get_llm(
        model_key: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        agent_name: str = "Agent",
    ) -> BaseChatModel:
        """
        Get configured LLM instance.

        Args:
            model_key: Key from MODELS dict ('groq_fast' or 'ollama_local')
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum tokens to generate
            agent_name: Name for logging callbacks

        Returns:
            Configured LLM instance
        """
        if model_key not in LLMConfig.MODELS:
            raise ValueError(f"Unknown model key: {model_key}. Use one of {list(LLMConfig.MODELS.keys())}")

        spec = LLMConfig.MODELS[model_key]
        provider = spec["provider"]

        # Common config
        callbacks = [LangChainLoggingHandler(agent_name=agent_name)]

        if provider == "groq":
            return RateLimitedGroq(
                model=spec["model"],
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=temperature,
                max_tokens=max_tokens or 4096,
                callbacks=callbacks,
            )

        elif provider == "ollama":
            return ChatOllama(
                model=spec["model"],
                temperature=temperature,
                num_predict=max_tokens or 4096,
                callbacks=callbacks,
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")


# ============================================================================
# Base Agent Class
# ============================================================================

class BaseAgent(ABC):
    """
    Abstract base class for all ANCA v2 agents.

    Provides common functionality:
    - Prompt loading
    - LLM configuration
    - Tool binding
    - Logging setup
    """

    def __init__(
        self,
        agent_name: str,
        prompt_file: str,
        model_key: str = "groq_fast",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize base agent.

        Args:
            agent_name: Name of the agent (for logging)
            prompt_file: Path to prompt YAML file (e.g., 'planning/topic_analysis.yaml')
            model_key: LLM model to use ('groq_fast' or 'ollama_local')
            temperature: Generation temperature
            max_tokens: Max tokens to generate
        """
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")

        # Load prompt configuration
        try:
            self.prompt_config = load_prompt(prompt_file)
            self.system_prompt = self.prompt_config.get("system_prompt", "")
            self.description = self.prompt_config.get("description", "")
        except FileNotFoundError:
            self.logger.warning(f"Prompt file not found: {prompt_file}. Using defaults.")
            self.prompt_config = {}
            self.system_prompt = ""
            self.description = ""

        # Configure LLM
        self.llm = LLMConfig.get_llm(
            model_key=model_key,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_name=agent_name,
        )

        self.logger.info(f"Initialized {agent_name} with model {model_key}")

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """
        Return list of tools this agent can use.

        Must be implemented by subclasses.
        """
        pass

    def create_react_agent(self) -> Any:
        """
        Create a LangGraph ReAct agent with this agent's LLM and tools.

        Returns:
            Compiled LangGraph agent
        """
        tools = self.get_tools()
        agent = create_react_agent(
            self.llm,
            tools,
            prompt=self.system_prompt,
        )
        self.logger.info(f"Created ReAct agent with {len(tools)} tools")
        return agent

    def log_execution(self, message: str):
        """Log agent execution step."""
        self.logger.info(f"[{self.agent_name}] {message}")

    def log_error(self, error: Exception):
        """Log agent error."""
        self.logger.error(f"[{self.agent_name}] Error: {error}", exc_info=True)


# ============================================================================
# Specialized Base Classes
# ============================================================================

class PlanningAgent(BaseAgent):
    """Base class for planning layer agents."""

    def __init__(self, agent_name: str, prompt_file: str, **kwargs):
        # Planning agents use fast Groq model
        super().__init__(
            agent_name=agent_name,
            prompt_file=f"planning/{prompt_file}",
            model_key="groq_fast",
            **kwargs,
        )


class ProductionAgent(BaseAgent):
    """Base class for production layer agents (section writers)."""

    def __init__(self, agent_name: str, prompt_file: str, **kwargs):
        # Production agents use fast Groq model for generation
        super().__init__(
            agent_name=agent_name,
            prompt_file=f"production/{prompt_file}",
            model_key="groq_fast",
            temperature=0.7,  # Higher temperature for creative writing
            **kwargs,
        )


class RefinementAgent(BaseAgent):
    """Base class for refinement layer agents (auditors, editors)."""

    def __init__(self, agent_name: str, prompt_file: str, **kwargs):
        # Refinement agents use local Ollama for cost efficiency
        super().__init__(
            agent_name=agent_name,
            prompt_file=f"refinement/{prompt_file}",
            model_key="ollama_local",
            temperature=0.2,  # Lower temperature for consistent evaluation
            **kwargs,
        )


# ============================================================================
# Node Wrapper Utilities
# ============================================================================

def create_node_wrapper(agent_factory_func, node_name: str):
    """
    Create a LangGraph node wrapper for an agent.

    Args:
        agent_factory_func: Function that creates the agent
        node_name: Name of the node (for logging)

    Returns:
        Node function compatible with LangGraph
    """

    def node_wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper function that executes the agent."""
        logger.info(f"--- {node_name} Node ---")

        try:
            agent = agent_factory_func()
            result = agent.invoke(state)
            return result
        except Exception as e:
            logger.error(f"Error in {node_name}: {e}", exc_info=True)
            # Return state unchanged on error to prevent pipeline failure
            return state

    return node_wrapper


# ============================================================================
# Utility Functions
# ============================================================================

def extract_from_messages(messages: List, pattern: str) -> Optional[str]:
    """
    Extract content from messages using regex pattern.

    Args:
        messages: List of LangChain messages
        pattern: Regex pattern to match

    Returns:
        First matched group or None
    """
    import re

    for msg in reversed(messages):
        content = msg.content if hasattr(msg, "content") else str(msg)
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1) if match.groups() else match.group(0)

    return None


def count_words(text: str) -> int:
    """
    Count words in markdown text (excluding code blocks and metadata).

    Args:
        text: Markdown text

    Returns:
        Word count
    """
    from tools.word_count_tool import count_markdown_words
    return count_markdown_words(text)
