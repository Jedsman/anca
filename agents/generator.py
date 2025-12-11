"""
Content Generator Node (LangGraph)
Uses native tool calling to write and save articles.
"""
import os
import logging
from typing import List
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from app.core.langchain_logging_callback import LangChainLoggingHandler
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

@tool
def retrieve_context(query: str):
    """Retrieve relevant context/facts from the knowledge base using a search query."""
    return rag._run(action="retrieve", query=query)

seen_queries = set()

@tool
def retrieve_context(query: str):
    """Retrieve relevant context/facts from the knowledge base using a search query."""
    # Normalize to prevent case/whitespace bypass
    q = query.strip().lower()
    if q in seen_queries:
        return f"SYSTEM NOTE: You have already searched for '{query}'. Do NOT search it again. Use a different query to retrieve the content need."
    seen_queries.add(q)
    return rag._run(action="retrieve", query=query)

@tool
def read_file(filename: str):
    """Read specific file content."""
    return file_reader._run(filename=filename)

# --- System Prompt for Tool-First Execution ---
GENERATOR_SYSTEM_PROMPT = """You are an autonomous content generation agent. You MUST follow these rules STRICTLY:

## EXECUTION RULES (MANDATORY)
1. **TOOL-FIRST**: Your FIRST response MUST be a tool call to `retrieve_context`. NEVER start with text.
2. **NO CONVERSATION**: Do NOT ask questions, seek clarification, or say "I will now...".
3. **NO PLANNING TEXT**: Do NOT output plans or explanations. Just execute tools.
4. **MANDATORY SAVE**: You MUST call `save_article` at the end. If you don't, you have FAILED.

## FORBIDDEN BEHAVIORS (WILL CAUSE FAILURE)
- ❌ "Would you like me to..."
- ❌ "I will now..."
- ❌ "Let me help you..."
- ❌ "Here's a plan..."
- ❌ Any question marks in your response
- ❌ Any text before your first tool call
- ❌ Ending without calling save_article

## CORRECT EXECUTION SEQUENCE
1. Call `retrieve_context(query="...")` with different queries to gather facts
2. Don't use the same query multiple times
3. Write the FULL 2000+ word article
4. Call `save_article(filename="...", content="...")` with the complete article

BEGIN EXECUTION NOW. NO TEXT. ONLY TOOL CALLS."""

# --- Node Factory ---
def create_generator_node():
    """Create the Generator agent as a LangGraph node."""

    # 1. Setup LLM
    llm = ChatOllama(
        model="qwen2.5:7b-instruct",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.7,
        num_ctx=10240,
        callbacks=[LangChainLoggingHandler(agent_name="Content Generator")]
    )

    # 2. Define Tools
    # Note: retrieval only, ingestion is done by Researcher
    tools = [save_article, retrieve_context, read_file]

    # 3. Create Agent with system prompt for tool-first behavior
    agent = create_react_agent(
        llm,
        tools,
        prompt=GENERATOR_SYSTEM_PROMPT
    )

    return agent
