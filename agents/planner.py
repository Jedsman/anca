import logging
from langchain_core.prompts import ChatPromptTemplate
from app.state import ArticleState, Blueprint, Section
from app.core.llm_wrappers import get_llm
from app.core.langchain_logging_callback import LangChainLoggingHandler
from app.core.agent_config import agent_config

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an expert Editor-in-Chief.
Your goal is to create a comprehensive content blueprint for a high-quality article.

You will be given a Topic (and potential context).
You must output a structured Blueprint containing:
1. Title: Engagement and SEO optimized.
2. Audience: Who is this for?
3. Sections: A logical flow of sections.

For EACH Section, you must provide:
- Heading: The section title.
- Description: Detailed instructions on what to cover.
- Word Count: Estimate (total article should be ~2000-2500 words).
- Search Queries: 2-3 specific queries to research this section.

## Guidelines:
- The article must be deep, authoritative, and engaging.
- Use a mix of long-form text, lists, and tables (implied in descriptions).
- If 'Affiliate Mode' is active, structure it as a Buyer's Guide (Intro, Methodology, Top Picks, Comparison, Buying Advice, Conclusion).
"""

def planner_node(state: ArticleState):
    logger.info(f"[PLANNER] Planning article for topic: {state['topic']}")
    
    # 1. Setup LLM
    ac = agent_config.get_agent_settings("planner")
    llm = get_llm(
        provider=state.get("provider") or ac.provider,
        model=state.get("model") or ac.model,
        temperature=0.7,
        callbacks=[LangChainLoggingHandler(agent_name="Planner")]
    )

    # 2. Configure Structured Output
    structured_llm = llm.with_structured_output(Blueprint)

    # 3. Create Prompt
    instructions = f"Topic: {state['topic']}"
    if state.get("affiliate", False):
        instructions += "\n\nCONTEXT: This is an AFFILIATE REVIEW article. You MUST structure it as a Buyer's Guide with a Comparison Table section and Pros/Cons for products."

    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", instructions),
    ])

    # 4. Invoke
    chain = prompt | structured_llm
    
    try:
        blueprint = chain.invoke({"topic": state["topic"]})
        logger.info(f"[PLANNER] Blueprint generated with {len(blueprint.sections)} sections.")
        return {"blueprint": blueprint}
    except Exception as e:
        logger.error(f"[PLANNER] Error generating blueprint: {e}")
        raise e
