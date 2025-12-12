import logging
import json
from langchain_core.prompts import ChatPromptTemplate
from app.state import ArticleState
from app.core.llm_wrappers import get_llm
from app.core.langchain_logging_callback import LangChainLoggingHandler
from app.core.topic_manager import TopicManager
from tools.search_tool import _duckduckgo_search

logger = logging.getLogger(__name__)

# --- System Prompts ---
SCOUT_SYSTEM_PROMPT = """You are a Trend Scout for a premium tech & lifestyle publication.
Your goal is to discover a "Rising Star" topic that is:
1.  **Fresh**: Gaining traction right now.
2.  **Substantial**: Complex enough for a 2,000-word deep dive.
3.  **Monetizable**: Related to products, software, or services.

You will be given a list of search results about current trends.
"""

SCOUT_SINGLE_PROMPT = """
You must analyze them and select ONE specific, high-potential topic.

Output Format: Just the topic string. No markdown, no quotes.
Example: The Rise of AI Wearables in 2024
"""

SCOUT_LIST_PROMPT = """
You must analyze them and propose 5 distinct, high-potential topics.

Output Format: A JSON list of strings.
Example: ["Topic A", "Topic B", "Topic C", "Topic D", "Topic E"]
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

NICHE_LIST_PROMPT = """
Select 5 specific, distinct topic strings.
Output Format: A JSON list of strings.
"""

def trend_analyzer_node(state: ArticleState):
    """
    Trend Analyzer Node:
    - If `niche` is None: Runs "Scout Mode" (Global discovery).
    - If `niche` is set: Runs "Niche Mode" (Targeted discovery).
    Updates `topic` in the state.
    """
    niche = state.get("niche")
    
    # 1. Setup LLM
    llm = get_llm(
        provider=state.get("provider", "gemini"),
        model=state.get("model", "gemini-flash-lite-latest"),
        temperature=0.7,
        callbacks=[LangChainLoggingHandler(agent_name="TrendAnalyzer")]
    )

    # 2. Research Phase
    topic_manager = TopicManager() 
    interactive = state.get("interactive", False)

    if niche:
        logger.info(f"[TREND ANALYZER] Running Niche Mode for: {niche}")
        query = f"top trends and new products in {niche} {2025}" 
        search_results = _duckduckgo_search(query, num_results=5)
        base_prompt = NICHE_SYSTEM_PROMPT.format(niche=niche)
        instruction_prompt = NICHE_LIST_PROMPT if interactive else NICHE_SINGLE_PROMPT
    else:
        logger.info("[TREND ANALYZER] Running Scout Mode (Global Discovery)")
        query = "breakthrough consumer technology trends and products 2024 2025"
        search_results = _duckduckgo_search(query, num_results=5)
        base_prompt = SCOUT_SYSTEM_PROMPT
        instruction_prompt = SCOUT_LIST_PROMPT if interactive else SCOUT_SINGLE_PROMPT

    # 3. Decision Phase
    logger.info(f"[TREND ANALYZER] Analyzed search results (Interactive={interactive})")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", base_prompt + instruction_prompt),
        ("human", f"Search Results:\n{search_results}\n\nIdentify the best topic(s) now:"),
    ])

    chain = prompt | llm
    
    try:
        response = chain.invoke({})
        content = response.content.strip()
        
        if interactive:
            # Parse list
            content = content.replace("```json", "").replace("```", "").strip()
            candidates = json.loads(content)
            
            # Filter duplicates
            valid_candidates = [t for t in candidates if not topic_manager.is_duplicate(t)]
            
            if not valid_candidates:
                logger.warning("[TREND ANALYZER] All candidates were duplicates. Returning raw list.")
                valid_candidates = candidates # Fallback
                
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
