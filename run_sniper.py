import argparse
import logging
from langgraph.graph import StateGraph, END
from app.state_sniper import ArbitrageState
from app.core.config_sniper import sniper_settings
from app.core.logging_sniper import get_sniper_logger

# Import Nodes
from agents.sniper.search import search_node
from agents.sniper.triage import triage_node
from agents.sniper.valuation import valuation_node
from agents.sniper.analysis import analysis_node
from agents.sniper.reflection import reflection_node
from agents.sniper.planner import planner_node
from agents.sniper.niche_discovery import niche_discovery_node

logger = get_sniper_logger("Sniper.Main")

# --- Router Logic ---
def route_planner(state: ArbitrageState):
    """
    After Planner, check if we have queries.
    If yes, go to Search (with first query).
    If no, End.
    """
    queries = state.get("pending_queries", [])
    if queries:
        next_query = queries.pop(0)
        state["search_query"] = next_query
        state["pending_queries"] = queries
        return "search"
    return END

def route_reflection(state: ArbitrageState):
    """
    After Reflection, check if we have more pending queries.
    If yes, loop back to Search.
    If no, End.
    """
    queries = state.get("pending_queries", [])
    if queries:
        next_query = queries.pop(0)
        state["search_query"] = next_query
        state["pending_queries"] = queries
        return "search"
    return END

# --- Workflow Definition ---
workflow = StateGraph(ArbitrageState)

workflow.add_node("niche_discovery", niche_discovery_node)
workflow.add_node("planner", planner_node)
workflow.add_node("search", search_node)
workflow.add_node("triage", triage_node)
workflow.add_node("valuation", valuation_node)
workflow.add_node("analysis", analysis_node)
workflow.add_node("reflection", reflection_node)

def route_start(state: ArbitrageState):
    # If explicit query exists, assume we want to process it or plan around it.
    if state.get("search_query"):
        # Could be a direct Search or a Niche for Planner.
        # If --auto was set (is_autonomous=True), treat input as Niche -> Planner.
        # If not, treat as Query -> Search.
        if state.get("is_autonomous"):
            return "planner"
        return "search"
    
    # If NO query, we must discover a niche first.
    return "niche_discovery"

workflow.set_conditional_entry_point(
    route_start,
    {
        "niche_discovery": "niche_discovery",
        "planner": "planner",
        "search": "search"
    }
)

# Edges
workflow.add_edge("niche_discovery", "planner")

workflow.add_conditional_edges(
    "planner",
    route_planner,
    {
        "search": "search",
        END: END
    }
)

workflow.add_edge("search", "triage")
workflow.add_edge("triage", "valuation")
workflow.add_edge("valuation", "analysis")
workflow.add_edge("analysis", "reflection")

workflow.add_conditional_edges(
    "reflection",
    route_reflection,
    {
        "search": "search",
        END: END
    }
)

app = workflow.compile()

def main():
    parser = argparse.ArgumentParser(description="eBay Sniper Agent")
    parser.add_argument("--query", type=str, help="Search query OR Niche. Optional if --discover is used.")
    parser.add_argument("--min-profit", type=float, default=10.0, help="Minimum profit setting")
    parser.add_argument("--auto", action="store_true", help="Enable Autonomous Mode (Treat query as Niche)")
    parser.add_argument("--discover", action="store_true", help="Full Discovery Mode (Find Niche -> Find Items)")
    parser.add_argument("--mock", action="store_true", help="Run with Mock Data (No API keys needed)")
    
    args = parser.parse_args()
    
    # Logic:
    # 1. User provides query + no flags -> Direct Search (classic).
    # 2. User provides query + --auto -> Niche Mode (Planner -> Search).
    # 3. User provides NO query (or --discover) -> Discovery Mode (NicheDiscovery -> Planner -> Search).
    
    if args.mock:
        sniper_settings.mock_ebay = True
        logger.warning("Starting in MOCK Mode - No Real API calls will be made.")
    
    if not args.query and not args.discover:
        # Default to discover if nothing provided? Or error?
        # User said "we don't need a query". So implicit discovery.
        args.discover = True
        
    sniper_settings.min_profit_margin = args.min_profit
    
    initial_state = {
        "search_query": args.query,
        "niche": None,
        "pending_queries": [],
        "raw_listings": [],
        "targets_for_valuation": [],
        "final_deals": [],
        "error_message": None,
        "is_complete": False,
        "is_autonomous": args.auto or args.discover
    }
    
    mode_str = "Full Discovery" if args.discover else ("Autonomous Niche" if args.auto else "Direct Search")
    logger.info(f"Starting Sniper. Mode: {mode_str}. Input: {args.query}")
    
    try:
        final_state = app.invoke(initial_state)
        
        print("\n----------------- SNIPER RUN COMPLETE -----------------")
        if final_state.get('niche'):
            print(f"Active Niche: {final_state['niche']}")
            
        deals = final_state.get("final_deals", [])
        # Note: This only prints deals from the LAST loop iteration.
        # Proper solution would be to accumulate deals in a separate state key.
        
    except Exception as e:
        logger.exception("Resulted in Critical Failure")
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
