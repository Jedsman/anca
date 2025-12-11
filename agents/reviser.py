"""
SEO Reviser Node (LangGraph)
Revises articles based on SEO auditor feedback. Focused on formatting, keywords, and structure.
Does NOT handle content expansion (that's the Critique agent's job).
"""
import os
import logging
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from app.core.langchain_logging_callback import LangChainLoggingHandler
from tools.file_writer_tool import FileWriterTool
from tools.file_reader_tool import FileReaderTool

logger = logging.getLogger(__name__)

# --- Tool Wrappers ---
file_writer = FileWriterTool()
file_reader = FileReaderTool()


@tool
def save_article(filename: str, content: str):
    """Save the revised markdown article to a file. Call this when the revision is complete."""
    if not content or len(content) < 50:
        return "Error: Content too short to save."
    return file_writer._run(filename=filename, content=content)


@tool
def read_file(filename: str):
    """Read the current article file to understand what SEO issues need to be fixed."""
    return file_reader._run(filename=filename)


# --- System Prompt for SEO-Focused Revision ---
SEO_REVISER_SYSTEM_PROMPT = """You are an autonomous SEO revision agent. You MUST follow these rules STRICTLY:

## YOUR ROLE
You handle **SEO-specific fixes only**:
- Keyword placement and density
- Heading hierarchy (H1 → H2 → H3)
- Meta formatting (bold key terms, bullet points)
- Readability improvements
- Adding missing sections (FAQ, Conclusion)

You do NOT handle content expansion or length issues. That is handled by a different agent.

## EXECUTION RULES (MANDATORY)
1. **TOOL-FIRST**: Your FIRST response MUST be a tool call to `read_file`. NEVER start with text.
2. **NO CONVERSATION**: Do NOT ask questions or say "I will now...".
3. **IMPLEMENT ALL SEO FIXES**: Address EVERY issue from the audit feedback.
4. **MANDATORY SAVE**: You MUST call `save_article` at the end with the FULL revised article.

## FORBIDDEN BEHAVIORS (WILL CAUSE FAILURE)
- ❌ "Would you like me to..."
- ❌ "I will now..."
- ❌ Any question marks in your response
- ❌ Any text before your first tool call
- ❌ Ending without calling save_article
- ❌ Partial revisions (you must save the COMPLETE article)

## CORRECT EXECUTION SEQUENCE
1. Call `read_file(filename="...")` to read the current article
2. Apply SEO fixes from the audit feedback
3. Call `save_article(filename="...", content="...")` with the FULL revised article

BEGIN EXECUTION NOW. NO TEXT. ONLY TOOL CALLS."""


# --- Node Factory ---
def create_seo_reviser_node():
    """Create the SEO Reviser agent as a LangGraph node."""

    # 1. Setup LLM
    llm = ChatOllama(
        model="qwen2.5:7b-instruct",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.3,  # Low creativity for SEO fixes
        num_ctx=10240,
        callbacks=[LangChainLoggingHandler(agent_name="SEO Reviser")]
    )

    # 2. Define Tools - NO RAG/Search, SEO fixes only
    tools = [save_article, read_file]

    # 3. Create Agent with system prompt for SEO-focused behavior
    agent = create_react_agent(
        llm,
        tools,
        prompt=SEO_REVISER_SYSTEM_PROMPT
    )

    return agent


# Keep old function name for backwards compatibility during transition
def create_reviser_node():
    """Deprecated: Use create_seo_reviser_node instead."""
    logger.warning("create_reviser_node is deprecated, use create_seo_reviser_node")
    return create_seo_reviser_node()
