from langchain_core.prompts import PromptTemplate
from app.state_sniper import ArbitrageState
from app.core.config_sniper import sniper_settings, get_sniper_llm
from app.core.logging_sniper import get_sniper_logger
import json

logger = get_sniper_logger("Sniper.Triage")

def triage_node(state: ArbitrageState):
    """
    Triage Node:
    Uses LLM to filter out junk (parts only, broken, etc).
    """
    raw_listings = state.get("raw_listings", [])
    if not raw_listings:
        logger.info("[TRIAGE] No listings to process.")
        state["targets_for_valuation"] = []
        return state

    logger.info(f"[TRIAGE] Filtering {len(raw_listings)} items via Ollama...")
    
    # Check if Ollama Base URL is reachable? 
    # Langchain might error if not.
    
    items_lite = [
        {"id": item['itemId'], "title": item['title'], "condition": item.get('condition', 'Unknown')}
        for item in raw_listings
    ]

    prompt = PromptTemplate.from_template(
        """
        You are an expert eBay flipper. Review the following items.
        Filter out any items that are:
        - "For parts" or "Not working"
        - "Broken" or "Damaged"
        - "Untested" (unless explicitly stated as likely working)
        - "Box only" or "Manual only"
        - "Empty Box"
        
        Return ONLY a JSON object with a single key "ids" containing the list of itemId strings for the items that are GOOD candidates (likely working, complete).
        
        Items:
        {items_json}
        
        Example Output:
        {{
            "ids": ["12345", "67890"]
        }}
        """
    )
    
    llm = get_sniper_llm("triage", temperature=0.0)
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"items_json": json.dumps(items_lite)})
        valid_ids_str = response.content
        data = json.loads(valid_ids_str)
        
        valid_ids = data.get("ids", [])
        
        # Filter the original list
        targets = [item for item in raw_listings if str(item['itemId']) in valid_ids]
        
        logger.info(f"[TRIAGE] Kept {len(targets)} out of {len(raw_listings)} items.")
        state["targets_for_valuation"] = targets
        
    except Exception as e:
        logger.error(f"[TRIAGE] LLM Error: {e}")
        # On error, return empty to be safe
        state["targets_for_valuation"] = []
        state["error_message"] = f"Triage Error: {str(e)}"

    return state
