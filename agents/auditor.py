"""
SEO Auditor Node (LangGraph)
Critiques content and provides feedback.
"""
import os
import logging
from typing import List
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from app.core.langchain_logging_callback import LangChainLoggingHandler
from tools.file_reader_tool import FileReaderTool

logger = logging.getLogger(__name__)

# --- Tool Wrappers ---
file_reader = FileReaderTool()

@tool
def read_article_file(filename: str):
    """Read the content of the drafted article file to audit it."""
    return file_reader._run(filename=filename)

# --- System Prompt for Tool-First Execution ---
AUDITOR_SYSTEM_PROMPT = """You are an autonomous SEO auditor agent. You MUST follow these rules STRICTLY:

## EXECUTION RULES (MANDATORY)
1. **TOOL-FIRST**: Your FIRST response MUST be a tool call to `read_article_file`. NEVER start with text.
2. **NO CONVERSATION**: Do NOT ask questions or say "I will now...".
3. **CRITICAL ANALYSIS**: Be harsh and specific in your critique. No empty praise.
4. **SCORE REQUIRED**: You MUST provide a "Quality Score: X/10" in your final output.

## FORBIDDEN BEHAVIORS (WILL CAUSE FAILURE)
- ❌ "Would you like me to..."
- ❌ "I will now..."
- ❌ Any question marks in your response
- ❌ Any text before your first tool call
- ❌ Ending without a Quality Score

## CORRECT EXECUTION SEQUENCE
1. Call `read_article_file(filename="...")` to read the article
2. Analyze against SEO and quality criteria
3. Output a structured critique with "Quality Score: X/10"

BEGIN EXECUTION NOW. NO TEXT. ONLY TOOL CALLS."""

# --- Node Factory ---
def create_auditor_node(system_prompt: str = AUDITOR_SYSTEM_PROMPT):
    """
    Create the Auditor agent as a LangGraph node.
    
    Args:
        system_prompt (str): The system prompt to use for the agent.
    """
    """Create the Auditor agent as a LangGraph node."""

    # 1. Setup LLM
    llm = ChatOllama(
        model="qwen2.5:7b-instruct",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.3,  # Low temp for critical analysis
        num_ctx=10240,
        callbacks=[LangChainLoggingHandler(agent_name="SEO Auditor")]
    )

    # 2. Define Tools
    # Auditor NEEDS to read the file to critique it properly
    tools = [read_article_file]

    # 3. Create Agent with system prompt for tool-first behavior
    agent = create_react_agent(
        llm,
        tools,
        prompt=system_prompt
    )

    return agent
