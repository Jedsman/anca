import logging
from langchain_core.prompts import ChatPromptTemplate
from app.state import ArticleState
from app.core.llm_wrappers import get_llm
from app.core.langchain_logging_callback import LangChainLoggingHandler

logger = logging.getLogger(__name__)

REFINER_SYSTEM_PROMPT = """You are a Senior Editor.
Your goal is to improve the article based on precise feedback from the Auditor or Fact Checker.

You will be given:
1.  The Original Article.
2.  The Feedback (Audit Critique or Factual Corrections).

CRITICAL: If factual errors are listed, YOU MUST FIX THEM. This is your top priority.

Instructions:
- Rewrite the article to address the feedback.
- **Tone**: Write like a generic human author. Avoid flowery "AI" language (e.g., "in the realm of", "tapestry", "leveraging").
- **Grammar**: Ensure impeccable grammar and flow.
- Maintain the original Markdown formatting (H1, H2, etc.).
- Do not make the article shorter unless requested.

Output ONLY the full rewritten article in Markdown.
"""

def refiner_node(state: ArticleState):
    # User requested Groq for Auditor/Refiner
    provider = "groq"
    model = "llama-3.3-70b-versatile"
    
    llm = get_llm(provider, model, temperature=0.7, callbacks=[LangChainLoggingHandler(agent_name="Refiner")])

    prompt = ChatPromptTemplate.from_messages([
        ("system", REFINER_SYSTEM_PROMPT),
        ("human", "Feedback: {feedback}\n\nOriginal Article:\n{article}\n\nRewrite the article now:"),
    ])

    chain = prompt | llm

    logger.info("[REFINER] Refining article based on feedback...")
    try:
        response = chain.invoke({
            "feedback": state["feedback"],
            "article": state["final_article"]
        })
        
        rewritten_article = response.content
        logger.info("[REFINER] Article refined.")
        
        # Save to file (overwrite)
        filename = state.get("filename")
        if filename:
             try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(rewritten_article)
                logger.info(f"[REFINER] Overwrote file: {filename}")
             except Exception as e:
                logger.error(f"[REFINER] Failed to save refined article: {e}")

        current_rev = state.get("revision_number", 0)
        return {
            "final_article": rewritten_article,
            "revision_number": current_rev + 1,
            "feedback": None # Clear feedback so Auditor creates new feedback
        }
        
    except Exception as e:
        logger.error(f"[REFINER] Error: {e}")
        return {} # No change on error
