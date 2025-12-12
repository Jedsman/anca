import os
import logging
from app.core.llm_wrappers import get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

from app.state import ArticleState, Blueprint
from app.core.langchain_logging_callback import LangChainLoggingHandler

logger = logging.getLogger(__name__)

# --- System Prompt ---
PLANNER_SYSTEM_PROMPT = """You are the Editor-in-Chief of a high-end publication.
Your goal is to plan a comprehensive, engaging, and deep article on the given topic.

## Instructions
1. Analyze the user's topic.
2. Design a logical structure (Blueprint) for the article.
3. Break it down into 5-7 distinct sections.
4. For EACH section, provide:
    *   `heading`: Catchy but clear title.
    *   `description`: Precise instructions on what this section must cover.
    *   `word_count`: Target length (usually 300-500 words).
    *   `search_queries`: 2-3 specific search terms for the researcher to find facts for *this specific section*.

## Rules
*   Ensure a logical flow (Introduction -> History/Background -> Core Concepts -> Advanced Details -> Conclusion).
*   The total word count should aim for 2000+ words.
*   Be specific in descriptions. Don't just say "Discuss X", say "Explain X by comparing it to Y and citing recent statistics".
"""

def planner_node(state: ArticleState):
    """
    Editor-in-Chief node: Generates the article blueprint.
    """
    logger.info(f"[PLANNER] Planning article for topic: {state['topic']}")

    # 1. Setup LLM
    llm = get_llm(
        provider=state.get("provider", "gemini"),
        model=state.get("model", "gemini-flash-lite-latest"),
        temperature=0.7,
        callbacks=[LangChainLoggingHandler(agent_name="Planner")]
    )

    # 2. Configure Structured Output
    # Gemini supports structured output natively or via LangChain's with_structured_output
    structured_llm = llm.with_structured_output(Blueprint)

    # 3. Create Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", PLANNER_SYSTEM_PROMPT),
        ("human", "Topic: {topic}"),
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
