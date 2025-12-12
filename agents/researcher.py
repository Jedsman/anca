"""
Market Researcher Node (LangGraph)
Uses Groq (Llama 3.3 70B) for fast research with 128K context.
"""
import os
import logging
from typing import List, Annotated
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from app.core.langchain_logging_callback import LangChainLoggingHandler
from app.core.rate_limiter import groq_rate_limiter
from tools.search_tool import web_search
from tools.scraper_tool import ScraperTool

from tools.rag_tool import RAGTool

logger = logging.getLogger(__name__)

# --- Tool Wrappers ---
scraper = ScraperTool()
rag = RAGTool()

@tool
def scrape_website(url: str):
    """Scrape content from a website URL. Returns a brief preview to help decide if the source is valuable."""
    result = scraper._run(url)
    # Return only a preview to avoid bloating the message history
    if isinstance(result, str) and len(result) > 1000:
        return f"[PREVIEW - {len(result)} chars total]\n{result[:1000]}...\n\n[Use ingest_content to add this to the knowledge base if it looks valuable]"
    return result

@tool
def ingest_content(url: str):
    """Ingest a URL into the RAG knowledge base. Use this for EVERY good URL you find."""
    return rag._run(action="ingest", url=url)

# --- System Prompt for Tool-First Execution ---
RESEARCHER_SYSTEM_PROMPT = """You are an autonomous research agent. Execute tools to find and ingest high-quality sources.

## RULES
1. Start by calling web_search to find relevant URLs
2. For each promising URL, call scrape_website to preview its content
3. For good sources, call ingest_content to add them to the knowledge base
4. Find 5-7 high-quality sources before finishing
5. Do NOT ask questions or seek clarification - just execute

Your goal: Find comprehensive, authoritative sources that can support a 2000+ word article."""

# --- Rate-Limited Groq Wrapper ---
class RateLimitedGroq(ChatGroq):
    """Groq wrapper with token bucket rate limiting."""

    def _generate(self, *args, **kwargs):
        logger.info("[GROQ-RESEARCHER] _generate called - acquiring rate limit token")
        groq_rate_limiter.acquire()
        try:
            result = super()._generate(*args, **kwargs)
            logger.info(f"[GROQ-RESEARCHER] _generate returned: {type(result)}")
            return result
        except Exception as e:
            logger.error(f"[GROQ-RESEARCHER] _generate error: {e}")
            raise


# --- Node Factory ---
def create_researcher_node():
    """Create the Researcher agent as a LangGraph node using Groq."""

    # 1. Setup LLM - Groq with rate limiting (128K context, much faster than local)
    llm = RateLimitedGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.3,  # Lower temperature for more deterministic tool use
        max_tokens=4096,  # Researcher outputs are short (tool calls + summaries)
        callbacks=[LangChainLoggingHandler(agent_name="Market Researcher")]
    )

    # 2. Define Tools
    tools = [web_search, scrape_website, ingest_content]

    # 3. Create Agent with system prompt for tool-first behavior
    agent = create_react_agent(
        llm,
        tools,
        prompt=RESEARCHER_SYSTEM_PROMPT
    )

    return agent
