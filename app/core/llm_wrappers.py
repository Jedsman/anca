from typing import Any, List, Optional
import os
import logging
from pydantic import PrivateAttr
from langchain_core.language_models import BaseChatModel

# Import Providers
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from app.core.rate_limiter import TokenBucket, gemini_rate_limiter, gemini_flash_lite_limiter, groq_rate_limiter

logger = logging.getLogger(__name__)

# --- Wrappers ---

class RateLimitedGemini(ChatGoogleGenerativeAI):
    """Gemini wrapper with token bucket rate limiting."""
    _rate_limiter: TokenBucket = PrivateAttr()

    def __init__(self, rate_limiter: TokenBucket, **kwargs):
        super().__init__(**kwargs)
        self._rate_limiter = rate_limiter

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._rate_limiter.acquire()
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        self._rate_limiter.acquire()
        return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)


class RateLimitedGroq(ChatGroq):
    """Groq wrapper with token bucket rate limiting."""
    _rate_limiter: TokenBucket = PrivateAttr()

    def __init__(self, rate_limiter: TokenBucket, **kwargs):
        super().__init__(**kwargs)
        self._rate_limiter = rate_limiter

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._rate_limiter.acquire()
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        self._rate_limiter.acquire()
        return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)


# --- Factory ---

def get_llm(provider: str, model: str, temperature: float = 0.7, callbacks: List[Any] = None) -> BaseChatModel:
    """
    Factory to get the appropriate LLM instance based on provider and model.
    
    Args:
        provider: 'gemini', 'groq', 'ollama'
        model: Model name string
        temperature: Generation temperature
        callbacks: LangChain callbacks
    
    Returns:
        Configured ChatModel configuration
    """
    provider = provider.lower()
    
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
            
        # Select Rate Limiter
        if "flash-lite" in model or "flash" in model: # Broad match for flash models
             limiter = gemini_flash_lite_limiter
             logger.info(f"Using Flash/Lite Rate Limiter for {model}")
        else:
             limiter = gemini_rate_limiter
             logger.info(f"Using Standard Rate Limiter for {model}")

        return RateLimitedGemini(
            model=model,
            rate_limiter=limiter,
            api_key=api_key,
            temperature=temperature,
            callbacks=callbacks
        )
        
    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
            
        return RateLimitedGroq(
            model=model,
            rate_limiter=groq_rate_limiter,
            api_key=api_key,
            temperature=temperature,
            callbacks=callbacks
        )
        
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature,
            num_ctx=10240,
            callbacks=callbacks
        )
        
    else:
        raise ValueError(f"Unsupported provider: {provider}")
