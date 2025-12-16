from app.state_sniper import ArbitrageState
from tools.ebay_tool import EbayTool
from app.core.logging_sniper import get_sniper_logger
import statistics

logger = get_sniper_logger("Sniper.Valuation")

def valuation_node(state: ArbitrageState):
    """
    Valuation Node:
    For each target, find the median sold price (TTV) of similar items.
    """
    targets = state.get("targets_for_valuation", [])
    if not targets:
        logger.info("[VALUATION] No targets to valuate.")
        return state

    ebay = EbayTool()
    evaluated_targets = []
    
    logger.info(f"[VALUATION] Calculating TTV for {len(targets)} items...")
    
    for item in targets:
        title = item.get('title')
        condition_id = item.get('conditionId')
        
        # Search for sold items
        # Optimization: We could relax the title search if strict match fails,
        # but for safety in arbitrage, strict(er) match is better.
        sold_items = ebay.find_completed_items(keywords=title, condition_id=condition_id, limit=10)

        # Check if no sold items were found (API limitation or no matches)
        if not sold_items:
            # Fallback (Path A): Active Competitor Valuation
            logger.info(f"[VALUATION] Zero sold history (API Limit). Trying Active Competitor check for: {title[:30]}...")
            try:
                lowest_bin = ebay.find_lowest_bin(keywords=title, condition_id=condition_id)

                if lowest_bin > 0:
                    item['ttv'] = lowest_bin
                    item['sold_comps_count'] = -1 # Flag as Active Estimate
                    logger.info(f"[VALUATION] Active Competitor Price for '{title[:20]}...': {lowest_bin}")
                else:
                    item['ttv'] = 0
            except AttributeError:
                logger.warning(f"[VALUATION] find_lowest_bin not yet implemented. Setting TTV to 0 for: {title[:30]}...")
                item['ttv'] = 0

            evaluated_targets.append(item)
            continue
            
        # Extract sold prices (Price + Shipping)
        # Note: sold_items returns 'sold_price' (item only).
        # We need total cost to buyer to estimate value? 
        # Actually TTV usually means "What are people willing to pay TOTAL".
        # If I sell it, I get (Sold Price + Shipping) - Fees - Shipping(if free).
        # Let's assume TTV = Item Price for simplicity, or SolPrice + Shipping.
        # Safest bet: Median of (Sold Price). Shipping is variable.
        # But if I sell, I charge shipping too. So comparison is (My Buy Price + My Ship Cost) vs (Sold Price).
        
        prices = []
        for sold in sold_items:
            # item['sold_price'] was set in _parse_item
            p = sold.get('sold_price')
            if p is not None:
                prices.append(p)
        
        if not prices:
            # Double Check Fallback here too if list existed but no prices
            try:
                lowest_bin = ebay.find_lowest_bin(keywords=title, condition_id=condition_id)
                if lowest_bin > 0:
                    item['ttv'] = lowest_bin
                    item['sold_comps_count'] = -1
                else:
                    item['ttv'] = 0
            except AttributeError:
                logger.warning(f"[VALUATION] find_lowest_bin not yet implemented. Setting TTV to 0 for: {title[:30]}...")
                item['ttv'] = 0
        else:
            median_price = statistics.median(prices)
            item['ttv'] = median_price
            item['sold_comps_count'] = len(prices)
            logger.info(f"[VALUATION] TTV for '{title[:20]}...': {median_price} (based on {len(prices)} solds)")
        
        evaluated_targets.append(item)
    
    state["targets_for_valuation"] = evaluated_targets
    return state
