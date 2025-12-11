"""
QA Critique Node (LangGraph)
Evaluates article quality and length, with access to RAG and Search for content expansion.
"""
import os
import logging
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from app.core.langchain_logging_callback import LangChainLoggingHandler
from tools.file_reader_tool import FileReaderTool
from tools.word_count_tool import calculate_word_count
from tools.rag_tool import RAGTool
from tools.search_tool import web_search

logger = logging.getLogger(__name__)

# --- Tool Wrappers ---
file_reader = FileReaderTool()
rag = RAGTool()


@tool
def read_file(filename: str):
    """Read the article file to evaluate its content."""
    return file_reader._run(filename=filename)


@tool
def retrieve_context(query: str):
    """Retrieve relevant context from the knowledge base to find additional content for expansion."""
    return rag._run(action="retrieve", query=query)


# --- System Prompt for Tool-First Execution ---
CRITIQUE_SYSTEM_PROMPT = """You are an autonomous QA Critique agent. You MUST follow these rules STRICTLY:

## EXECUTION RULES (MANDATORY)
1. **TOOL-FIRST**: Your FIRST response MUST be a tool call to `read_file`. NEVER start with text.
2. **MEASURE FIRST**: After reading, call `calculate_word_count` to get the exact word count.
3. **NO CONVERSATION**: Do NOT ask questions or say "I will now...".
4. **STRUCTURED OUTPUT**: You MUST provide a "Status: PASS" or "Status: FAIL" in your final output.

## FORBIDDEN BEHAVIORS (WILL CAUSE FAILURE)
- ❌ "Would you like me to..."
- ❌ "I will now..."
- ❌ Any question marks in your response
- ❌ Any text before your first tool call
- ❌ Ending without a Status verdict

## CORRECT EXECUTION SEQUENCE
1. Call `read_file(filename="...")` to read the article
2. Call `calculate_word_count(markdown_content="...")` with the article text
3. Evaluate against quality criteria (word count, section completeness)
4. If FAIL: Call `retrieve_context` or `web_search` to gather expansion material
5. Output structured critique with "Status: PASS" or "Status: FAIL"

## PASS/FAIL CRITERIA
- **Word Count**: Must be >= target (usually 1800 words)
- **Sections**: Must have Intro, Definition, Benefits, How-To, Mistakes, FAQ, Conclusion
- If either criterion fails, the status is FAIL

BEGIN EXECUTION NOW. NO TEXT. ONLY TOOL CALLS."""


# --- Node Factory ---
def create_critique_node():
    """Create the Critique agent as a LangGraph node."""

    # 1. Setup LLM
    llm = ChatOllama(
        model="qwen2.5:7b-instruct",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.2,  # Low temp for consistent evaluation
        num_ctx=10240,
        callbacks=[LangChainLoggingHandler(agent_name="QA Critique")]
    )

    # 2. Define Tools - includes RAG and Search for content expansion
    tools = [read_file, calculate_word_count, retrieve_context, web_search]

    # 3. Create Agent with system prompt for tool-first behavior
    agent = create_react_agent(
        llm,
        tools,
        prompt=CRITIQUE_SYSTEM_PROMPT
    )

    return agent
