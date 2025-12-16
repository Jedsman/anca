from app.state_sniper import ArbitrageState
from tools.ebay_tool import EbayTool
from app.core.logging_sniper import get_sniper_logger

logger = get_sniper_logger("Sniper.Search")

def search_node(state: ArbitrageState):
    """
    Search Node:
    Queries eBay for items ending soon with low bids.
    """
    # Logic:
    # 1. If we have pending_queries (from Planner), use the next one.
    # 2. If we have a category_id (from NicheDiscovery), use that.
    # 3. Else use search_query.
    
    query = state.get("search_query")
    category_id = state.get("category_id")
    
    ebay = EbayTool()
    items = []

    if category_id:
        logger.info(f"[SEARCH] Surfing Category ID: {category_id}")
        items = ebay.find_active_auctions(category_ids=category_id, max_results=50)
    elif query:
        logger.info(f"[SEARCH] Querying: {query}")
        items = ebay.find_active_auctions(keywords=query, max_results=50)
    else:
        logger.warning("[SEARCH] No query or category_id found.")

    logger.info(f"[SEARCH] Found {len(items)} raw items.")
    state["raw_listings"] = items
    
    return state
