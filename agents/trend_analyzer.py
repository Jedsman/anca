import logging
import json
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.state import ArticleState
from app.core.llm_wrappers import get_llm
from app.core.langchain_logging_callback import LangChainLoggingHandler
from app.core.topic_manager import TopicManager
from tools.search_tool import _duckduckgo_search
from app.core.agent_config import agent_config

logger = logging.getLogger(__name__)

# --- System Prompts ---
SCOUT_SYSTEM_PROMPT = """You are a Trend Scout for a leading high quality publication.
Your goal is to discover a "Rising Star" topic that is:
1.  **Fresh**: Gaining traction right now.
2.  **Substantial**: Complex enough for a 2,000-word deep dive.
3.  **Monetizable**: Related to products, software, or services.

You will be given a list of search results about current trends.

## Commercial Intent Scoring
For each topic, assign a score (1-10):
- **10/10**: "Best X for Y", "X vs Y Review". (High buyer intent).
- **1/10**: "History of X", "How X works". (Informational only).
"""

SCOUT_SINGLE_PROMPT = """
You must analyze them and select ONE specific, high-potential topic.

Output Format: Just the topic string. No markdown, no quotes.
Example: The Rise of AI Wearables in 2024
"""

SCOUT_LIST_PROMPT = """
You must analyze them and propose 10 distinct, high-potential topics.

Output Format: A JSON list of objects: [{{"topic": "Title", "score": 8}}, ...]
IMPORTANT: Output ONLY the valid JSON list. Do NOT produce a numbered list or any conversational text.
"""

TOPIC_DISCOVERY_SYSTEM_PROMPT = """You are an Affiliate Topic Discovery Specialist.
Current Date: {current_date}

Your goal: Identify exactly 10 HIGH-POTENTIAL affiliate content opportunities in the niche: "{niche}"

## SELECTION CRITERIA (ALL must be met):

### 1. COMMERCIAL INTENT (8-10/10 required)
✓ GOOD: "Best [product] for [specific problem/audience]", "[Product A] vs [Product B] for [use case]", "Top [product] for [year]"
✗ BAD: "What is [topic]", "History of [topic]", "How [topic] works", "Guide to understanding [topic]"

### 2. MONETIZATION VALIDATION
✓ Products likely cost £50-£500 (affiliate sweet spot)
✓ Multiple brands/options exist (comparison content possible)
✓ Clear product categories (not services or abstract concepts)

### 3. CONTENT OPPORTUNITY (Look for these signals):
✓ Existing top results are thin (<1500 words) or outdated (>18 months old)
✓ Generic listicles without specific use cases or comparisons
✓ No hands-on testing evidence in top results
✓ Missing key comparison angles (price ranges, specific audiences, use cases)

### 4. SPECIFICITY TEST
✓ GOOD: "Best noise-cancelling headphones for open offices under £200"
✓ GOOD: "Standing desks for small apartments 2025"
✗ BAD: "Best headphones" (too broad)
✗ BAD: "Office furniture guide" (too vague)

### 5. AVOID THESE RED FLAGS:
✗ Dominated by major publishers (Wirecutter, Forbes, CNET) in all top 10 spots
✗ Medical/health claims requiring professional credentials
✗ Purely B2B enterprise software (complex sales cycles, no affiliate programs)
✗ Trending fads with <6 months lifespan

## SCORING FRAMEWORK (Rate each topic 1-10):

**Commercial Intent** (Weight: 40%)
- 10: Direct comparison/review with purchase intent ("X vs Y for Z")
- 8: Best-of with qualifier ("Best X for Y 2025")
- 6: Recommendation request ("Which X should I buy for Y")
- 3: Problem-solution (may not lead to purchase)
- 1: Pure information ("What is X")

**Competition Level** (Weight: 30%, inverse scoring)
- 10: Weak content, outdated articles, thin affiliate sites dominate
- 7: Mix of weak and strong content
- 4: Some authoritative sites but gaps exist
- 1: All top 10 are Wirecutter/Forbes/major publishers

**Content Differentiation** (Weight: 30%)
- 10: Unique angle others completely miss
- 8: Specific audience/use case underserved
- 6: Can add detail/testing to generic content
- 3: Crowded, hard to differentiate
- 1: Nothing new to say

**COMPOSITE SCORE = (Commercial * 0.4) + (Competition * 0.3) + (Differentiation * 0.3)**

## OUTPUT FORMAT (STRICT JSON):
Provide a list of objects. Do not wrap in markdown code blocks.
[
  {{
    "topic": "Best Standing Desks for Small Apartments 2025",
    "commercial_intent": 9,
    "competition": 8,
    "differentiation": 8,
    "composite_score": 8.4,
    "reasoning": "High buyer intent, existing content is generic.",
    "content_gap": "Top results don't address cable management for small spaces.",
    "monetization_confidence": "High - Amazon Associates, FlexiSpot programs"
  }}
]

CRITICAL: Only output valid JSON. Start with [ and end with ]. No preamble.
"""

TOPIC_DISCOVERY_USER_PROMPT = """
Based on these search results for "{niche}", identify the 10 best affiliate content opportunities.

Search Results:
{search_results}

Remember:
- Focus on BUYING INTENT topics only
- Verify products exist in the £50-£500 range
- Output JSON array of exactly 10 topics, ranked by composite score.
"""

NICHE_SYSTEM_PROMPT = """You are a Niche Analyst.
Your goal is to find the most engaging, "must-read" topic within the niche: "{niche}".

Criteria:
1.  **High Intent**: Something people are actively unsure about (e.g., "Best X for Y").
2.  **Low Competition / High Detail**: A specific angle that generic articles miss.
3.  **Timeliness**: Relevant to current discussions.

You will be given search results about this niche.
"""

NICHE_SINGLE_PROMPT = """
Select ONE specific topic string.
Output Format: Just the topic string.
"""

NICHE_SINGLE_PROMPT = """
Select ONE specific topic string.
Output Format: Just the topic string.
"""

NICHE_LIST_PROMPT = """
Select 10 specific, distinct topic strings.
Output Format: A JSON list of objects: [{{"topic": "Title", "score": 8}}, ...]
IMPORTANT: Output ONLY the valid JSON list. Do NOT produce a numbered list.
"""

QUERY_GEN_PROMPT = """You are a Search Query Expert.
Your goal is to generate 3 Google search queries to discover {goal}.

Context:
- Niche: {niche}
- Affiliate Mode: {affiliate} (If True, focus on "Best", "Review", "High Ticket", "VS").

Output Format: A JSON list of 3 strings.
Example: ["best ai wearables 2025", "smart ring comparison", "new tech gadgets 2025"]
"""

def trend_analyzer_node(state: ArticleState):
    """
    Trend Analyzer Node:
    1. Generates Search Queries (LLM).
    2. Searches DuckDuckGo.
    3. Analyzes results to pick 1-5 Topics.
    """
    niche = state.get("niche")
    
    niche = state.get("niche")
    
    # 1. Setup LLM
    ac = agent_config.get_agent_settings("trend_analyzer")
    llm = get_llm(
        provider=state.get("provider") or ac.provider,
        model=state.get("model") or ac.model,
        temperature=0.7,
        callbacks=[LangChainLoggingHandler(agent_name="TrendAnalyzer")]
    )

    # 2. Research Phase
    topic_manager = TopicManager() 
    interactive = state.get("interactive", False)
    affiliate = state.get("affiliate", False)

    # 2a. Generate Queries
    goal_desc = "rising consumer trends" if not affiliate else "high-ticket affiliate product opportunities"
    niche_desc = niche if niche else "Global Consumer Trends (Technology, Home, Health, Lifestyle)"
    
    logger.info(f"[TREND ANALYZER] Generating queries for: {niche_desc} (Affiliate={affiliate})")

    query_prompt = ChatPromptTemplate.from_messages([
        ("system", QUERY_GEN_PROMPT),
        ("human", "Generate queries now."),
    ])
    
    query_chain = query_prompt | llm
    try:
        q_response = query_chain.invoke({
            "niche": niche_desc,
            "affiliate": str(affiliate),
            "goal": goal_desc
        })
        # Parse queries
        import re
        q_content = q_response.content.strip()
        match = re.search(r'\[.*\]', q_content, re.DOTALL)
        queries = json.loads(match.group(0) if match else q_content)
        queries = queries[:3] # Limit to 3
    except Exception as e:
        logger.error(f"[TREND ANALYZER] Query Gen failed: {e}. Using fallback.")
        queries = ["top rated tech gadgets 2025 reviews"]

    # 2b. Execute Search
    search_results = ""
    for q in queries:
        logger.info(f"[TREND ANALYZER] Searching: {q}")
        res = _duckduckgo_search(q, num_results=6) # Increased to ensure enough source material
        search_results += f"### Results for '{q}':\n{res}\n\n"

    # 2c. Select Prompt
    if niche:
        # Use Affiliate Prompt if flag is set
        base_prompt = "" # Prompt is handled dynamically in Decision Phase based on affiliate flag
        instruction_prompt = NICHE_LIST_PROMPT if interactive else NICHE_SINGLE_PROMPT
    else:
        base_prompt = TOPIC_DISCOVERY_SYSTEM_PROMPT if affiliate else SCOUT_SYSTEM_PROMPT
        instruction_prompt = SCOUT_LIST_PROMPT if interactive else SCOUT_SINGLE_PROMPT

    # 3. Decision Phase
    current_date_str = datetime.now().strftime('%B %Y')
    logger.info(f"[TREND ANALYZER] Analyzed search results (Interactive={interactive})")
    
    if affiliate:
        prompt = ChatPromptTemplate.from_messages([
            ("system", TOPIC_DISCOVERY_SYSTEM_PROMPT),
            ("human", TOPIC_DISCOVERY_USER_PROMPT),
        ])
        input_vars = {
            "niche": niche_desc, # Use the description we used for queries
            "search_results": search_results,
            "current_date": current_date_str
        }
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", base_prompt + instruction_prompt),
            ("human", f"Search Results:\n{search_results}\n\nIdentify the best topic(s) now:"),
        ])
        input_vars = {}

    chain = prompt | llm
    
    try:
        response = chain.invoke(input_vars)
        content = response.content.strip()
        logger.info(f"[TREND ANALYZER] Raw LLM Output: {content}")
        
        if interactive:
            # Parse list
            import re
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                content = match.group(0)
            
            content = content.replace("```json", "").replace("```", "").strip()
            candidates_data = json.loads(content) 
            
            # Normalize to list of strings first for dedup checking
            # Handle both string list (legacy) and object list (new)
            candidates = []
            if candidates_data and isinstance(candidates_data[0], dict):
                 # New format with scores
                 affiliate_mode = state.get("affiliate", False)
                 min_score = 6 if affiliate_mode else 0
                 
                 for item in candidates_data:
                     try:
                        # Handle new composite score key or fallback to simple score
                        score = item.get("composite_score", item.get("score", 0))
                        if score >= min_score:
                            candidates.append(item["topic"])
                     except:
                        continue
            else:
                candidates = candidates_data

            # Filter duplicates
            valid_candidates = [t for t in candidates if not topic_manager.is_duplicate(t)]
            
            if not valid_candidates:
                logger.warning("[TREND ANALYZER] All candidates were duplicates or low score. Returning raw list.")
                valid_candidates = [c["topic"] for c in candidates_data] if isinstance(candidates_data[0], dict) else candidates_data
                
            logger.info(f"[TREND ANALYZER] Generated {len(valid_candidates)} candidates")
            return {"topic_candidates": valid_candidates, "topic": valid_candidates[0]} # Default to first
            
        else:
            # Single topic
            topic = content.strip('"')
            if topic_manager.is_duplicate(topic):
                 logger.warning(f"[TREND ANALYZER] Topic '{topic}' is a duplicate but proceeding in non-interactive mode.")
            
            logger.info(f"[TREND ANALYZER] Discovered Topic: {topic}")
            return {"topic": topic}
        
    except Exception as e:
        logger.error(f"[TREND ANALYZER] Error generating topic: {e}")
        fallback = f"The Future of {niche if niche else 'Technology'}"
        return {"topic": fallback, "topic_candidates": [fallback]}
