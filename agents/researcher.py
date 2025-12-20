"""
Market Researcher Node (LangGraph)
Uses native tool calling to find and verify sources.
"""
import os
import logging
from typing import List, Annotated
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from app.core.langchain_logging_callback import LangChainLoggingHandler
from tools.search_tool import web_search
from tools.scraper_tool import ScraperTool

from tools.rag_tool import RAGTool

logger = logging.getLogger(__name__)

# --- Tool Wrappers ---
scraper = ScraperTool()
rag = RAGTool()

@tool
def scrape_website(url: str):
    """Scrape content from a website URL. Use this to verify if a URL is good."""
    return scraper._run(url)

@tool
def ingest_content(url: str):
    """Ingest a URL into the RAG knowledge base. Use this for EVERY good URL you find."""
    return rag._run(action="ingest", url=url)

# --- System Prompt for Tool-First Execution ---
RESEARCHER_SYSTEM_PROMPT = """You are an autonomous research agent. You MUST follow these rules STRICTLY:

## EXECUTION RULES (MANDATORY)
1. **TOOL-FIRST**: Your FIRST response MUST be a tool call. NEVER start with text.
2. **NO CONVERSATION**: Do NOT ask questions, seek clarification, or say "I will now...".
3. **NO PLANNING TEXT**: Do NOT output plans or explanations. Just execute tools.
4. **SILENT EXECUTION**: Execute tools silently. Only output results at the end.

## FORBIDDEN BEHAVIORS (WILL CAUSE FAILURE)
- ❌ "Would you like me to..."
- ❌ "I will now search for..."
- ❌ "Let me help you..."
- ❌ "Before I begin..."
- ❌ Any question marks in your response
- ❌ Any text before your first tool call

## CORRECT BEHAVIOR
Your response should IMMEDIATELY start with a tool call. Example:
[tool_call: web_search(query="...")]

BEGIN EXECUTION NOW. NO TEXT. ONLY TOOL CALLS."""

# --- Node Factory ---
def create_researcher_node(system_prompt: str = RESEARCHER_SYSTEM_PROMPT):
    """
    Create the Researcher agent as a LangGraph node.
    
    Args:
        system_prompt (str): The system prompt to use for the agent.
    """

    # 1. Setup LLM
    llm = ChatOllama(
        model="qwen2.5:7b-instruct",
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.3,  # Lower temperature for more deterministic tool use
        num_ctx=10240,
        callbacks=[LangChainLoggingHandler(agent_name="Market Researcher")]
    )

    # 2. Define Tools
    tools = [web_search, scrape_website, ingest_content]

    # 3. Create Agent with system prompt for tool-first behavior
    agent = create_react_agent(
        llm,
        tools,
        prompt=system_prompt
    )

    return agent
