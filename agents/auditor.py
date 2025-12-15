import logging
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.state import ArticleState
from app.core.llm_wrappers import get_llm
from app.core.langchain_logging_callback import LangChainLoggingHandler

logger = logging.getLogger(__name__)

class AuditResult(BaseModel):
    pass_audit: bool = Field(description="True if the article is excellent and needs no changes (score > 85/100). False if revision is needed.")
    feedback: str = Field(description="Detailed instructions on what to fix. Be specific. If pass_audit is True, simple praise.")

AUDITOR_SYSTEM_PROMPT = """You are a strict SEO Auditor and Editor-in-Chief.
Review the article provided below.

Criteria:
1.  **Keyword Optimization**: Is the main topic clearly the focus in the H1 and intro?
2.  **Structure**: logic flow, proper H2/H3 usage.
3.  **Depth**: Does it cover the topic comprehensively?
4.  **Tone & Style**: Does it sound NATURAL and HUMAN? (Fail if it uses overused AI words like "delve", "realm", "symphony", "testament").
5.  **Conclusion**: Does it wrap up effectively?
6.  **Grammar**: Is it grammatically perfect?

If the article is good, pass it.
If the article is weak, repetitive, or missing key info, fail it and provide specific instructions for the Refiner.
"""

from app.core.agent_config import agent_config

def auditor_node(state: ArticleState):
    # 1. Setup LLM
    ac = agent_config.get_agent_settings("auditor")
    # Allow override but default to config (which defaults to Groq)
    provider = state.get("provider") or ac.provider
    model = state.get("model") or ac.model
    
    # Force JSON output or use structured output if available
    llm = get_llm(provider, model, temperature=0.1, callbacks=[LangChainLoggingHandler(agent_name="Auditor")])
    structured_llm = llm.with_structured_output(AuditResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", AUDITOR_SYSTEM_PROMPT),
        ("human", "Topic: {topic}\n\nArticle:\n{article}\n\nAudit this article:"),
    ])

    chain = prompt | structured_llm

    logger.info("[AUDITOR] Auditing article...")
    try:
        result = chain.invoke({
            "topic": state["topic"],
            "article": state["final_article"]
        })
        
        feedback = result.feedback if not result.pass_audit else None
        logger.info(f"[AUDITOR] Result: Pass={result.pass_audit}")
        return {
            "feedback": feedback,
            "revision_number": state.get("revision_number", 0) # incremented in refiner or handled in edge? Handled in graph state updates usually.
        }
        
    except Exception as e:
        logger.error(f"[AUDITOR] Error: {e}")
        # Default pass to avoid infinite error loops
        return {"feedback": "Error during audit. Passing by default.", "revision_number": 0}
