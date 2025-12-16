from app.state_sniper import ArbitrageState
from app.core.config_sniper import sniper_settings, get_sniper_llm
from app.core.logging_sniper import get_sniper_logger
from langchain_core.prompts import PromptTemplate
import json

logger = get_sniper_logger("Sniper.Reflection")

def reflection_node(state: ArbitrageState):
    """
    Reflection Node:
    Reviews final deals for red flags and adds confidence scores.
    Acts as a quality gate before presenting deals to user.

    Checks for:
    - Scam indicators (price too good to be true)
    - Data quality issues (low comp count, TTV reliability)
    - Title red flags (broken, parts, etc.)
    - Category-specific risks (counterfeits)

    Adds confidence scores: "high", "medium", "low"
    """
    deals = state.get("final_deals", [])

    # Skip if no deals or reflection disabled
    if not deals or not sniper_settings.reflection_enabled:
        if not deals:
            logger.info("[REFLECTION] No deals to review.")
        else:
            logger.info("[REFLECTION] Reflection disabled, passing through all deals.")
        return state

    logger.info(f"[REFLECTION] Reviewing {len(deals)} deals for quality assurance...")

    # Prepare deal summaries for LLM review
    deals_summary = []
    for idx, deal in enumerate(deals):
        analysis = deal.get("analysis", {})
        deals_summary.append({
            "index": idx,
            "title": deal.get("title", "Unknown"),
            "current_price": deal.get("price", 0),
            "shipping": deal.get("shipping_cost", 0),
            "total_cost": analysis.get("cost_basis", 0),
            "ttv": deal.get("ttv", 0),
            "profit": analysis.get("profit", 0),
            "roi": analysis.get("roi_percent", 0),
            "comps_count": deal.get("sold_comps_count", 0),
            "condition": deal.get("condition", "Unknown"),
            "price_ratio": analysis.get("price_ratio", 0)
        })

    prompt = PromptTemplate.from_template(
        """
        You are a risk assessment expert for eBay arbitrage deals.
        Review these potential deals and identify red flags or quality concerns.

        Deals to review:
        {deals_json}

        For EACH deal, evaluate:

        1. **SCAM INDICATORS** (immediate rejection):
           - Price ratio < 0.15 (current price less than 15% of market value)
           - ROI > 400% (unrealistic profit margin)
           - Total cost < $5 for expensive items (likely scam)

        2. **DATA QUALITY** (affects confidence):
           - comps_count < 3 (low sample size, unreliable TTV)
           - comps_count = -1 (TTV is estimate from active listings, not sold items)
           - comps_count = 0 (no data at all)

        3. **TITLE RED FLAGS** (check for hidden issues):
           - Contains: "broken", "parts", "not working", "as-is", "untested"
           - Contains: "read description", "see photos", "sold as is"
           - Missing important details

        4. **CATEGORY RISKS** (common counterfeit items):
           - Electronics: iPhone, AirPods, Samsung Galaxy at steep discount
           - Designer items: Gucci, Louis Vuitton, Rolex at low prices
           - Collectibles: Rare cards, autographs without authentication

        Assign confidence level:
        - "high": Safe to bid, good data, realistic pricing
        - "medium": Proceed with caution, verify condition/seller
        - "low": Risky, likely scam or data quality issues - REJECT

        Return ONLY valid JSON with this structure:
        {{
            "validated_deals": [
                {{"index": 0, "confidence": "high", "reason": "Strong comps (8), realistic 45% ROI, good condition"}},
                {{"index": 1, "confidence": "medium", "reason": "Only 2 comps, verify item condition before bidding"}}
            ],
            "rejected_deals": [
                {{"index": 2, "confidence": "low", "reason": "Price ratio 0.12 - likely scam, too good to be true"}},
                {{"index": 3, "confidence": "low", "reason": "Title contains 'parts only' - missed by triage"}}
            ]
        }}

        Be conservative - better to reject a questionable deal than let a scam through.
        """
    )

    llm = get_sniper_llm("reflection", temperature=0.3)
    chain = prompt | llm

    try:
        response = chain.invoke({"deals_json": json.dumps(deals_summary, indent=2)})
        result = json.loads(response.content)

        validated = result.get("validated_deals", [])
        rejected = result.get("rejected_deals", [])

        # Build final deals list with confidence scores
        final_deals = []
        for v in validated:
            idx = v["index"]
            if idx < len(deals):
                deal = deals[idx].copy()
                deal["confidence"] = v["confidence"]
                deal["reflection_notes"] = v["reason"]
                final_deals.append(deal)

                confidence_emoji = {
                    "high": "[HIGH CONFIDENCE]",
                    "medium": "[MEDIUM CONFIDENCE]",
                    "low": "[LOW CONFIDENCE]"
                }.get(v["confidence"], "")

                logger.info(
                    f"[REFLECTION] {confidence_emoji} VALIDATED: "
                    f"{deal['title'][:40]} - {v['reason']}"
                )

        # Log rejected deals for learning/debugging
        rejected_deals_data = []
        for r in rejected:
            idx = r["index"]
            if idx < len(deals):
                rejected_deal = {
                    "deal": deals[idx],
                    "reason": r["reason"],
                    "confidence": r.get("confidence", "low")
                }
                rejected_deals_data.append(rejected_deal)

                logger.warning(
                    f"[REFLECTION] REJECTED: "
                    f"{deals[idx]['title'][:40]} - {r['reason']}"
                )

        # Update state
        state["final_deals"] = final_deals
        state["rejected_deals"] = rejected_deals_data

        logger.info(
            f"[REFLECTION] Complete - "
            f"Validated: {len(final_deals)}, "
            f"Rejected: {len(rejected_deals_data)}"
        )

    except json.JSONDecodeError as e:
        logger.error(f"[REFLECTION] JSON parsing error: {e}, passing through original deals")
        # Fail-open: on JSON error, keep original deals
    except Exception as e:
        logger.error(f"[REFLECTION] Error during reflection: {e}, passing through original deals")
        # Fail-open: on any error, keep original deals to avoid blocking user

    return state
