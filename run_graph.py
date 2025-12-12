import logging
import operator
from typing import Annotated, List, TypedDict

from langgraph.graph import StateGraph, END, START
from langgraph.types import Send

from app.state import ArticleState
from app.core.config import settings
from app.core.logging_utils import get_session_log_file, AnsiStrippingFormatter

# --- Agents ---
from agents.planner import planner_node
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.assembler import assembler_node

# Setup Logger
logger = logging.getLogger(__name__)

# --- Map Logic ---
def map_sections(state: ArticleState):
    """
    Map the Blueprint sections to parallel Writer nodes.
    """
    blueprint = state["blueprint"]
    return [
        Send("writer", {
            "section": section, 
            "order": i,
            "provider": state.get("provider", "gemini"),
            "model": state.get("model", "gemini-flash-lite-latest")
        }) 
        for i, section in enumerate(blueprint.sections)
    ]

# --- Graph Definition ---
workflow = StateGraph(ArticleState)

workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("assembler", assembler_node)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "researcher")
workflow.add_conditional_edges("researcher", map_sections, ["writer"])
workflow.add_edge("writer", "assembler")
workflow.add_edge("assembler", END)

app = workflow.compile()

# --- Logging Setup ---
def _setup_logging():
    """Setup logging for standalone execution with rotation"""
    import logging
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = get_session_log_file("gemini_map_reduce", settings.logs_dir)
    file_formatter = AnsiStrippingFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(settings.log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger.info(f"[LOG] Logs will be written to: {log_file}")

# --- Execution ---
if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="Run GEMINI Map-Reduce Content Generator")
    parser.add_argument("--topic", type=str, default="How to make cold brew coffee", help="Topic to write about")
    parser.add_argument("--provider", type=str, default="gemini", help="LLM Provider: gemini, groq, ollama")
    parser.add_argument("--model", type=str, default="gemini-flash-lite-latest", help="Model name")
    args = parser.parse_args()

    _setup_logging()
    
    print(f"Starting GEMINI Map-Reduce Workflow for topic: {args.topic}")
    
    # Run the graph
    # LangGraph invoke is synchronous by default but can handle async nodes if configured
    # Our nodes are sync (though they use async LLM calls wrapped in sync `invoke`? No, ChatGoogleGenerativeAI invoke is sync)
    
    final_state = app.invoke({
        "topic": args.topic,
        "provider": args.provider,
        "model": args.model,
        # blueprint and sections_content are populated by nodes
        "sections_content": [] 
    })
    
    print("\n\n----------------- FINAL ARTICLE -----------------\n")
    print(final_state["final_article"][:500] + "...\n(Attributes truncated)")
    print("-------------------------------------------------")
    print(f"Full article saved.")
