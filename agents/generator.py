"""
Content Generator Node (LangGraph)
Uses Groq (Llama 3.3 70B) for long-form content generation with rate limiting.
"""
import os
import logging
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from app.core.langchain_logging_callback import LangChainLoggingHandler
from app.core.rate_limiter import groq_rate_limiter
from tools.file_writer_tool import FileWriterTool
from tools.rag_tool import RAGTool
from tools.file_reader_tool import FileReaderTool

logger = logging.getLogger(__name__)

# --- Tool Wrappers ---
file_writer = FileWriterTool()
rag = RAGTool()
file_reader = FileReaderTool()


@tool
def save_article(filename: str, content: str):
    """Save the full markdown article to a file. Call this ONLY when the article is complete and formatted."""
    if not content or len(content) < 50:
        return "Error: Content too short to save."
    return file_writer._run(filename=filename, content=content)


# Track seen queries to prevent duplicates
seen_queries = set()


@tool
def retrieve_context(query: str):
    """Retrieve relevant context/facts from the knowledge base using a search query."""
    # Normalize to prevent case/whitespace bypass
    q = query.strip().lower()
    if q in seen_queries:
        return f"SYSTEM NOTE: You have already searched for '{query}'. Do NOT search it again. Use a different query to retrieve the content needed."
    seen_queries.add(q)
    return rag._run(action="retrieve", query=query)


@tool
def read_file(filename: str):
    """Read specific file content."""
    return file_reader._run(filename=filename)


# --- Rate-Limited Groq Wrapper ---
class RateLimitedGroq(ChatGroq):
    """Groq wrapper with token bucket rate limiting."""

    def _generate(self, *args, **kwargs):
        logger.info("[GROQ] _generate called - acquiring rate limit token")
        groq_rate_limiter.acquire()
        try:
            result = super()._generate(*args, **kwargs)
            logger.info(f"[GROQ] _generate returned: {type(result)}")
            return result
        except Exception as e:
            logger.error(f"[GROQ] _generate error: {e}")
            raise

    def invoke(self, *args, **kwargs):
        logger.info("[GROQ] invoke called")
        try:
            result = super().invoke(*args, **kwargs)
            logger.info(f"[GROQ] invoke returned message type: {type(result)}")
            if hasattr(result, 'tool_calls'):
                logger.info(f"[GROQ] Tool calls: {result.tool_calls}")
            if hasattr(result, 'content'):
                logger.info(f"[GROQ] Content preview: {str(result.content)[:200]}...")
            return result
        except Exception as e:
            logger.error(f"[GROQ] invoke error: {e}")
            raise


# --- System Prompt for Content Generation ---
GENERATOR_SYSTEM_PROMPT = """You are an autonomous content generation agent. Your job is to write a comprehensive article.

## EXECUTION STEPS
1. Call retrieve_context multiple times with different queries to gather facts from the knowledge base
2. Write a FULL 2000+ word article using the retrieved information
3. Call save_article with the filename and complete article content

## RULES
- Do NOT ask questions or seek clarification
- Do NOT output planning text - just execute
- You MUST call save_article at the end with the complete article
- The article must be comprehensive, well-structured, and at least 2000 words"""


# --- Node Factory ---
def create_generator_node():
    """Create the Generator agent as a LangGraph node using Groq."""

    # 1. Setup LLM - Groq with rate limiting
    llm = RateLimitedGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7,
        max_tokens=8192,  # Enough for full 2000+ word article
        callbacks=[LangChainLoggingHandler(agent_name="Content Generator")]
    )

    # 2. Define Tools
    tools = [save_article, retrieve_context, read_file]

    # 3. Create Agent with system prompt for tool-first behavior
    agent = create_react_agent(
        llm,
        tools,
        prompt=GENERATOR_SYSTEM_PROMPT
    )

    return agent
