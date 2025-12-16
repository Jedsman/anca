from app.state_sniper import ArbitrageState
from app.core.config_sniper import sniper_settings
from app.core.logging_sniper import get_sniper_logger

logger = get_sniper_logger("Sniper.Analysis")

def analysis_node(state: ArbitrageState):
    """
    Analysis Node:
    Calculates profit margins and filters final deals.
    """
    targets = state.get("targets_for_valuation", [])
    if not targets:
        state["final_deals"] = []
        return state
        
    final_deals = []
    
    settings = sniper_settings
    
    logger.info("[ANALYSIS] Analyzing profit margins...")
    
    for item in targets:
        ttv = item.get('ttv', 0)
        price_obj = item.get('price', 0)
        shipping = item.get('shipping_cost', 0)
        
        current_cost = price_obj + shipping
        
        if ttv <= 0:
            continue
            
        # Formula:
        # Revenue = TTV * 0.87 (approx 13% ebay fees)
        # Expected Net = Revenue - Shipping_to_buyer (Assume buyer pays shipping, so we break even on that? Or Free Shipping? For simple arb, assume buyer pays ship)
        # So Net Pocket = TTV * 0.87.
        # Cost = Current Price + Shipping to Me.
        # Profit = Net Pocket - Cost.
        
        revenue = ttv * 0.87
        profit = revenue - current_cost
        
        # Avoid div by zero
        roi = (profit / current_cost) * 100 if current_cost > 0 else 0
        
        # Criteria
        # 1. Profit > MinThreshold (e.g. $10)
        # 2. BuyPrice / TTV ratio (e.g. < 0.7) - Logic: if ratio is high, margin is slim.
        
        price_ratio = current_cost / ttv if ttv > 0 else 999
        
        if profit >= settings.min_profit_margin and price_ratio <= settings.max_price_ratio:
            item['analysis'] = {
                "profit": round(profit, 2),
                "roi_percent": round(roi, 2),
                "cost_basis": current_cost,
                "market_value": ttv,
                "price_ratio": round(price_ratio, 2)
            }
            final_deals.append(item)
            logger.info(f"[ANALYSIS] DEAL FOUND: {item['title'][:40]} | Profit: ${profit:.2f} | TTV: ${ttv}")
            
    state["final_deals"] = final_deals
    state["is_complete"] = True # Finished cycle
    
    logger.info(f"[ANALYSIS] Found {len(final_deals)} deals.")
    return state
