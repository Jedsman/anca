import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator
from app.state import ArticleState
from app.core.llm_wrappers import get_llm
from app.core.langchain_logging_callback import LangChainLoggingHandler

logger = logging.getLogger(__name__)

from typing import Union

class FactCheckResult(BaseModel):
    # Allow bool or string "True"/"False" to be resilient to LLM output
    has_errors: Union[bool, str] = Field(description="True if there are SEVERE factual errors.")
    error_details: str = Field(description="List of specific errors found and the CORRECTION. If no errors, write 'None'.")

    @field_validator('has_errors', mode='before')
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() == 'true'
        return v

FACT_CHECKER_SYSTEM_PROMPT = """You are a Digital Fact Checker.
Your job is to verify the claims in the article.

## Focus Areas
1.  **Dates**: Release dates, event dates.
2.  **Product Names**: Verify exact spelling and model numbers.
3.  **Statistics/Prices**: Check if numbers are plausible.
4.  **Hallucinations**: Ensure cited studies or events actually exist.

## Instructions
- If the article is factually sound, return has_errors=False.
- If you find errors, return has_errors=True and list the errors with corrections.
- Do NOT nitpick style or grammar. Focus ONLY on objective facts.
"""

from app.core.agent_config import agent_config

def fact_checker_node(state: ArticleState):
    # 1. Setup LLM
    ac = agent_config.get_agent_settings("fact_checker")
    provider = state.get("provider") or ac.provider
    model = state.get("model") or ac.model
    
    llm = get_llm(provider, model, temperature=0.0, callbacks=[LangChainLoggingHandler(agent_name="FactChecker")])
    structured_llm = llm.with_structured_output(FactCheckResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", FACT_CHECKER_SYSTEM_PROMPT),
        ("human", "Topic: {topic}\n\nArticle to Check:\n{article}\n\nVerify facts:"),
    ])

    chain = prompt | structured_llm

    logger.info("[FACT CHECKER] Verifying claims...")
    try:
        result = chain.invoke({
            "topic": state["topic"],
            "article": state["final_article"]
        })
        
        if result.has_errors and result.error_details.lower() != "none":
            logger.warning(f"[FACT CHECKER] Found errors: {result.error_details[:100]}...")
            return {
                "fact_errors": result.error_details,
                "feedback": f"CRITICAL FACTUAL ERRORS FOUND:\n{result.error_details}\n\nPlease fix these immediately." 
                # We inject into feedback too so Refiner sees it easily if we reuse the same prompt logic
            }
        else:
            logger.info("[FACT CHECKER] No severe errors found.")
            return {
                "fact_errors": None,
                # Keep feedback None so we don't trigger refiner loop yet (unless Auditor does later)
            }
        
    except Exception as e:
        logger.error(f"[FACT CHECKER] Error: {e}")
        return {"fact_errors": None}
