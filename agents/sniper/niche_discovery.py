from app.state_sniper import ArbitrageState
from tools.search_tool import _duckduckgo_search # Using existing tool if available or fallback
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from app.core.config_sniper import sniper_settings
from app.core.logging_sniper import get_sniper_logger
import re

logger = get_sniper_logger("Sniper.NicheDiscovery")

def niche_discovery_node(state: ArbitrageState):
    """
    Niche Discovery Node:
    Autonomously finds a high-potential niche to target using Web Search + LLM.
    """
    logger.info("[NICHE] Starting autonomous Category Surfing...")
    
    # "Shotgun Strategy": Pick a random high-value category
    # 293 = Consumer Electronics
    # 625 = Cameras & Photo
    # 1249 = Video Games & Consoles
    # 15032 = Cell Phones & Smartphones
    # 11450 = Clothing, Shoes & Accessories (too broad?)
    # 1 = Collectibles
    
    import random
    categories = [
        {"id": "293", "name": "Consumer Electronics"},
        {"id": "625", "name": "Cameras & Photo"},
        {"id": "1249", "name": "Video Games & Consoles"},
        {"id": "15032", "name": "Cell Phones"},
        {"id": "1", "name": "Collectibles"}
    ]
    
    # Pick one
    chosen = random.choice(categories)
    
    logger.info(f"[NICHE] Surfing Category: {chosen['name']} (ID: {chosen['id']})")
    
    # We set 'search_query' to None because we search by Category ID
    # We store the cat ID in the state? Or we put it in search_query with a prefix?
    # Let's add a state field 'category_id' or overload search_query.
    # Cleaner to update state definition, but for MVP let's overload search_query 
    # to be "CATEGORY_ID:{id}" or just handle it in Search Node.
    
    # State update
    state["niche"] = chosen['name'] 
    state["category_id"] = chosen['id']
    state["search_query"] = None # No keyword needed
    
    return state
