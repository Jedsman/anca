from app.state_sniper import ArbitrageState
from app.core.constants import MOCK_LISTINGS # To be defined? Or just input
from langchain_core.prompts import PromptTemplate
from app.core.config_sniper import sniper_settings, get_sniper_llm
from app.core.logging_sniper import get_sniper_logger
import json

logger = get_sniper_logger("Sniper.Planner")

def planner_node(state: ArbitrageState):
    """
    Planner Node:
    Generates search queries based on the broad 'search_query' (Niche) provided by the user.
    """
    niche = state.get("niche") or state.get("search_query")
    
    logger.info(f"[PLANNER] Generating queries for niche: {niche}")
    
    if sniper_settings.mock_ebay:
        logger.warning("[MOCK] Returning mock queries for Planner.")
        state["pending_queries"] = ["Mock Query 1", "Mock Query 2"]
        return state

    prompt = PromptTemplate.from_template(
        """
        You are an expert eBay flipper specializing in {niche}.
        
        GOAL: specific search queries to find undervalued items.
        
        STRATEGY 1: POPULAR MODELS
        - Identify 2 specific, high-demand models (e.g. "Canon AE-1").
        
        STRATEGY 2: TYPOS & MISSPELLINGS (The Error Strategy)
        - For the identified models, generate 1 common misspelling/typo version that a sloppy seller might use.
        
        STRATEGY 3: BULK / LOTS (The Bulk Strategy)
        - Generate 1 query for a "Job Lot" or "Bundle" of these items (e.g. "Canon Camera Lot").
        
        Return ONLY a JSON object with a key "queries" containing the list of 4-5 strings.
        
        Example Output:
        {{
            "queries": ["Canon AE-1", "Canon AE1 Program", "Cannon AE-1", "Canon Camera Lot", "Vintage Camera Bundle"]
        }}
        """
    )
    
    llm = get_sniper_llm("planner", temperature=0.7)
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"niche": niche})
        data = json.loads(response.content)
        queries = data.get("queries", [])
        
        logger.info(f"[PLANNER] Generated {len(queries)} queries: {queries}")
        
        # We need to store these queries in the state so the Search node can use them.
        # However, the Search Node currently takes `state["search_query"]` (single string).
        # We need to adapt the graph to handle multiple queries.
        # Strategy: The Planner replaces the single 'search_query' with a list 'pending_queries'.
        # Then we iterate? Or we map?
        # For MVP, let's just picking the FIRST one to start, or change state to hold list.
        
        state["pending_queries"] = queries
        
    except Exception as e:
        logger.error(f"[PLANNER] Error generating queries: {e}")
        state["pending_queries"] = []

    return state
