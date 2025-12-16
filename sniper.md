---

| #📝 Software Design Document: AI Arbitrage Agent (Minimal API Use)##1. 🎯 Goal and Constraints | Field                                                                                                                                                                                          | Description |
| ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **Primary Goal**                                                                               | Identify items on eBay that are currently listed significantly below their established historical selling price (True Market Value) to facilitate low-volume online arbitrage for side income. |
| **Core Constraint**                                                                            | **Minimize API Calls** to stay within the free tier limit of the eBay Developer Program (5,000 calls/day for development/low-volume). Avoid mass trawling.                                     |
| **Platform**                                                                                   | Local Python application using **LangGraph** for orchestration and a local **Ollama** model for LLM reasoning/triage.                                                                          |
| **Dependencies**                                                                               | `langchain`, `langgraph`, `ollama`, `ebaysdk`, `pydantic` (for data validation).                                                                                                               |

##2. ⚙️ Agent Architecture (LangGraph State and Nodes)###A. Graph State (`ArbitrageAgentState`)This is the shared data object that passes through all nodes:

| Field                   | Type         | Description                                                                |
| ----------------------- | ------------ | -------------------------------------------------------------------------- |
| `search_query`          | `str`        | The current keywords being used (e.g., "Vintage Game Console").            |
| `raw_listings`          | `list[dict]` | The _filtered_ output from the Search Tool (current auctions ending soon). |
| `targets_for_valuation` | `list[dict]` | Listings that passed the initial LLM Triage and need their TTV calculated. |
| `final_deals`           | `list[dict]` | Listings where the profit margin exceeds the minimum threshold.            |
| `error_message`         | `str`        | Used for debugging or logging API failures.                                |

###B. Graph Nodes and FunctionsThe agent will operate in a cyclical graph with the following nodes:

| Node Name                 | Associated Function              | Description / Efficiency Strategy                                                                                                                                                                |
| ------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Start / Refine Search** | `update_query(state)`            | Starts the process or, if no deals are found, the LLM refines the `search_query` to try a different angle (e.g., adds "Rare" or changes category).                                               |
| **Search eBay**           | `search_current_listings(state)` | **EFFICIENT:** Calls the eBay API with specific filters (Auction, Ending Soonest, Low Bids, Low Price Range) to return only a highly targeted list (e.g., \leq 50 items).                        |
| **Triage LLM Filter**     | `triage_listings(state)`         | **EFFICIENT:** The local LLM processes `raw_listings` (the \leq 50 items) to discard clear non-starters (e.g., "For Parts," "Untested," bundles). Output populates `targets_for_valuation`.      |
| **Valuate TTV**           | `calculate_ttv(state)`           | **EFFICIENT:** Iterates **only** through `targets_for_valuation`. Calls the eBay **Sold Items API** (the more expensive call) only for the best items to find their **True Market Value (TTV)**. |
| **Analyze Profit**        | `analyze_profit(state)`          | Calculates the final profit margin and risk score for each item in `targets_for_valuation`. If threshold is met, appends to `final_deals`.                                                       |
| **Alert User**            | `send_alert(state)`              | Triggers a final alert (e.g., print to console) when `final_deals` is non-empty.                                                                                                                 |

| ###C. Conditional Edges (The Router) | Source Node                                             | Condition                | Destination Node |
| ------------------------------------ | ------------------------------------------------------- | ------------------------ | ---------------- |
| **Analyze Profit**                   | `if final_deals is not empty`                           | **Alert User**           |
| **Analyze Profit**                   | `if targets_for_valuation is empty and deals are empty` | **Refine Search** (Loop) |
| **Alert User**                       | `on finish`                                             | **END**                  |

##3. 💾 Tool Specifications (The Python Functions)###A. `search_current_listings(state)`\* **API:** eBay Finding API (or newer Browse API).

- **Key Parameters (for efficiency):**
- `keywords`: From `state.search_query`.
- `itemFilter.listingType`: **`Auction`**
- `sortOrder`: **`EndTimeSoonest`**
- `itemFilter.maxPrice`: Calculated heuristically (e.g., \approx 25\% of estimated TTV for the category).
- `itemFilter.minBids`: **`[0..2]`** (Focus on items with few bids).

###B. `calculate_ttv(state)`\* **API:** eBay Finding API (`findCompletedItems`).

- **Key Parameters:**
- `keywords`: The specific title of the targeted item.
- `itemFilter.listingType`: **`Auction`**
- `itemFilter.itemCondition`: Should match the listing's condition (e.g., `Used`).
- `sortOrder`: **`PricePlusShippingHighest`** (Then take the median of the top 10).

- **Output:** Returns a list of the 10 most recent sold prices. The function calculates and adds a `median_sold_price` key to the item dict.

###C. `triage_listings(state)`\* **Model:** Local LLM (Ollama).

- **Prompt Template:** "Review the following eBay item titles and descriptions. Return a filtered list of only those items that have no mention of 'for parts', 'untested', or 'broken'. Only return the clean, likely-to-be-working items."
- **Input:** `state.raw_listings`.
- **Output:** Sets `state.targets_for_valuation`.

##4. 🚀 DeploymentThe final step is to use this document to prompt Gemini to generate the Python boilerplate.

- **Initial Prompt to Gemini:** "Based on the provided Software Design Document for the 'AI Arbitrage Agent', generate the complete Python code using `langgraph` and the `ebaysdk` library. Include Pydantic models for the `ArbitrageAgentState` and the helper dicts."

The video linked below provides a tutorial on using the eBay Finding and Merchandising APIs with Python, which is the foundational code you will need to generate for your `ebaysdk` tools.

You can get an introduction to the eBay API and Python coding in this video: [Python code example for eBay API (Finding and Merchandising)](https://www.youtube.com/watch?v=RNLGY26fcoQ).
