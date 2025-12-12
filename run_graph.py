import logging
import operator
from typing import Annotated, List, TypedDict

from langgraph.graph import StateGraph, END, START
from langgraph.types import Send

from app.state import ArticleState
from app.core.config import settings
from app.core.logging_utils import get_session_log_file, AnsiStrippingFormatter
from app.core.topic_manager import TopicManager

# --- Agents ---
from agents.planner import planner_node
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.planner import planner_node
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.assembler import assembler_node
from agents.trend_analyzer import trend_analyzer_node
from agents.auditor import auditor_node
from agents.refiner import refiner_node
from agents.fact_checker import fact_checker_node

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

workflow.add_node("trend_analyzer", trend_analyzer_node)
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("assembler", assembler_node)
workflow.add_node("auditor", auditor_node)
workflow.add_node("refiner", refiner_node)
workflow.add_node("fact_checker", fact_checker_node)

def route_start(state: ArticleState):
    if state.get("niche") or state.get("discover_mode"):
        return "trend_analyzer"
    return "planner"

def route_trend_analyzer(state: ArticleState):
    if state.get("only_discovery"):
        return END
    return "planner"

workflow.add_conditional_edges(START, route_start, ["trend_analyzer", "planner"])
workflow.add_conditional_edges("trend_analyzer", route_trend_analyzer, ["planner", END])
def check_audit_result(state: ArticleState):
    feedback = state.get("feedback")
    rev = state.get("revision_number", 0)
    MAX_REVISIONS = 3 # Increased to 3 to allow fact checks + audits
    
    if feedback and rev < MAX_REVISIONS:
        return "refiner"
    return END

def check_facts_result(state: ArticleState):
    fact_errors = state.get("fact_errors")
    rev = state.get("revision_number", 0)
    MAX_REVISIONS = 3
    
    # If explicit fact corrections exist, Refine.
    if fact_errors and rev < MAX_REVISIONS:
        return "refiner"
    return "auditor"

workflow.add_edge("planner", "researcher")
workflow.add_conditional_edges("researcher", map_sections, ["writer"])
workflow.add_edge("writer", "assembler")
workflow.add_edge("assembler", "fact_checker")
workflow.add_conditional_edges("fact_checker", check_facts_result, ["refiner", "auditor"])
workflow.add_conditional_edges("auditor", check_audit_result, ["refiner", END])
workflow.add_edge("refiner", "fact_checker") # Always verify facts again after refinement

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
    parser.add_argument("--topic", type=str, default="", help="Topic to write about")
    parser.add_argument("--provider", type=str, default="gemini", help="LLM Provider: gemini, groq, ollama")
    parser.add_argument("--model", type=str, default="gemini-flash-lite-latest", help="Model name")
    parser.add_argument("--niche", type=str, default="", help="Broad niche for targeted discovery")
    parser.add_argument("--discover", action="store_true", help="Enable global trend discovery (Scout Mode)")
    parser.add_argument("--only-discovery", action="store_true", help="Halt after discovering topic")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive topic selection")
    args = parser.parse_args()

    _setup_logging()
    
    print(f"Starting GEMINI Map-Reduce Workflow for topic: {args.topic}")
    
    # --- Execution Logic ---
    initial_topic = args.topic
    
    # Interactive Mode Handling
    if args.interactive and (args.discover or args.niche):
        print(f"\n[INTERACTIVE] Running Trend Analyzer in {'Niche' if args.niche else 'Scout'} Mode...")
        
        # Manually run the node to get candidates
        temp_state = {
            "niche": args.niche if args.niche else None,
            "topic": "",
            "interactive": True,
            "provider": args.provider,
            "model": args.model
        }
        
        result = trend_analyzer_node(temp_state)
        candidates = result.get("topic_candidates", [result.get("topic")])
        
        print("\n----------------- CANDIDATE TOPICS -----------------")
        for i, cand in enumerate(candidates):
            print(f"{i+1}. {cand}")
        print("----------------------------------------------------\n")
        
        while True:
            try:
                choice = input("Select a topic (enter number) or 'q' to quit: ")
                if choice.lower() == 'q':
                    print("Exiting.")
                    exit(0)
                idx = int(choice) - 1
                if 0 <= idx < len(candidates):
                    initial_topic = candidates[idx]
                    print(f"\nSelected: {initial_topic}")
                    break
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a number.")
        
        # Disable discovery mode since we have a topic now
        args.discover = False 
        args.niche = ""

    # Run the graph
    final_state = app.invoke({
        "topic": initial_topic,
        "niche": args.niche if args.niche else None,
        "provider": args.provider,
        "model": args.model,
        # Flags for routing
        "discover_mode": args.discover, 
        "only_discovery": args.only_discovery,
        "interactive": args.interactive,
        # Blueprint populated by nodes
        "sections_content": [] 
    })
    
    print("\n\n----------------- FINAL ARTICLE -----------------\n")
    if final_state.get("final_article"):
        print(final_state["final_article"][:500] + "...\n(Attributes truncated)")
        print("-------------------------------------------------")
        print(f"Full article saved.")
        
        # Save to TopicHistory
        tm = TopicManager()
        tm.save_topic(final_state["topic"], niche=final_state.get("niche"))
        
    else:
        print("(No article generated - run halted or failed)")
        if final_state.get("topic"):
            print(f"Final Topic: {final_state['topic']}")
