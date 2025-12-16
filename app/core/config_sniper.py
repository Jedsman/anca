from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class SniperSettings(BaseSettings):
    """Configuration for eBay Sniper Agent"""
    
    # eBay API Credentials
    ebay_app_id: str = ""
    ebay_cert_id: str = ""
    ebay_dev_id: str = ""
    # Optional: Token might be needed for some calls, though Finding API usually uses AppID
    
    # Sniper Logic Defaults
    min_profit_margin: float = 10.0
    max_price_ratio: float = 0.7  # Max BuyPrice / TTV
    
    # Flags
    mock_ebay: bool = False
    ebay_sandbox: bool = False

    # Ollama (Legacy - kept for backward compatibility)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Agent-Specific LLM Models
    triage_provider: str = "ollama"  # "ollama", "groq", or "gemini"
    triage_model: str = "gemma2:9b-instruct"

    planner_provider: str = "ollama"  # "ollama", "groq", or "gemini"
    planner_model: str = "llama3.1:8b-instruct"

    niche_provider: str = "ollama"  # "ollama", "groq", or "gemini"
    niche_model: str = "mixtral:8x7b-instruct-v0.1"
    niche_use_llm: bool = False  # Set True to enable LLM-based niche discovery

    # Reflection Agent (Quality assurance for deals)
    reflection_provider: str = "ollama"  # "ollama", "groq", or "gemini"
    reflection_model: str = "gemma2:9b-instruct"
    reflection_enabled: bool = True  # Set False to skip reflection

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Allow existing env vars to coexist

sniper_settings = SniperSettings()


def get_sniper_llm(agent_name: str, temperature: float = 0.0):
    """
    Get LLM for sniper agent with proper provider/model configuration.
    Uses existing llm_wrappers.get_llm() factory with rate limiting.

    Args:
        agent_name: "triage", "planner", "niche", or "reflection"
        temperature: Generation temperature (0.0 for deterministic, 0.7 for creative)

    Returns:
        Configured LLM instance with rate limiting (if applicable)
    """
    from app.core.llm_wrappers import get_llm as base_get_llm

    if agent_name == "triage":
        provider = sniper_settings.triage_provider
        model = sniper_settings.triage_model
    elif agent_name == "planner":
        provider = sniper_settings.planner_provider
        model = sniper_settings.planner_model
    elif agent_name == "niche":
        provider = sniper_settings.niche_provider
        model = sniper_settings.niche_model
    elif agent_name == "reflection":
        provider = sniper_settings.reflection_provider
        model = sniper_settings.reflection_model
    else:
        raise ValueError(f"Unknown agent: {agent_name}")

    # Use existing factory with rate limiting (groq_rate_limiter at 30 RPM)
    llm = base_get_llm(provider=provider, model=model, temperature=temperature)

    # Add JSON format for Ollama (Groq uses model_kwargs in base_get_llm)
    if provider == "ollama" and hasattr(llm, 'format'):
        llm.format = "json"

    return llm
