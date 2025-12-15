import logging
import json
from langchain_core.prompts import ChatPromptTemplate
from app.state import ArticleState, Section
from app.core.llm_wrappers import get_llm
from app.core.langchain_logging_callback import LangChainLoggingHandler
from app.core.agent_config import agent_config
from tools.rag_tool import RAGTool

logger = logging.getLogger(__name__)

WRITER_SYSTEM_PROMPT = """You are a Senior Technical Writer.
Your task is to write ONE section of an article based on the provided Heading, Context, and Description.

## Input Context
You have access to:
- Heading and Description (from the Editor's plan).
- Research Context (snippets from search results).

## Output Requirements
- Write ONLY the content for this section. Do NOT include the heading (it will be added by the assembler).
- Use Markdown formatting (bold, lists, tables).
- Be conversational but authoritative.
- Cite sources if they are provided in the context (e.g. [Source]).
- Follow the Word Count target strictly (don't be too short, don't be too verbose).
"""

def writer_node(state: dict, section: Section, order: int):
    """
    Writer Node (Parallel execution per section).
    Note: In LangGraph, we typically map this function over sections.
    This function should return a partial update to 'sections_content'.
    """
    # 1. Setup LLM
    ac = agent_config.get_agent_settings("writer")
    
    provider = state.get("provider") or ac.provider
    model = state.get("model") or ac.model

    llm = get_llm(
        provider=provider,
        model=model,
        temperature=0.7,
        callbacks=[LangChainLoggingHandler(agent_name=f"Writer-{section.heading[:10]}")]
    )

    # 2. Perform Research (Deterministic)
    # We instantiate RAGTool here. Note: In nested parallel execution, ensure thread safety or new instance.
    rag = RAGTool()
    context_parts = []
    
    # Execute the queries planned by the Editor-in-Chief
    for query in section.search_queries:
        logger.info(f"[WRITER] Searching: {query}")
        try:
            result = rag._run(action="retrieve", query=query)
            context_parts.append(f"--- Query: {query} ---\n{result}\n")
        except Exception as e:
            logger.error(f"[WRITER] Search failed for '{query}': {e}")
    
    full_context = "\n".join(context_parts)
    if not full_context:
         full_context = "No specific research results found."

    # 3. Create Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_SYSTEM_PROMPT),
        ("human", "Heading: {heading}\nWord Count Target: {word_count}\nDescription: {description}\n\nResearch Context:\n{context}\n\nWrite the section now:"),
    ])
    
    # 4. Generate
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "heading": section.heading,
            "word_count": section.word_count,
            "context": full_context,
            "description": section.description
        })
        
        content = response.content
        logger.info(f"[WRITER] Section '{section.heading}' written ({len(content)} chars).")
        
        formatted_section = f"## {section.heading}\n\n{content}\n\n"
        
        # Return structured output for the map-reduce accumulator
        # We must return a dict with the key matching the state field we want to update.
        # In LangGraph map-reduce, this return value is aggregated.
        return {"sections_content": [{"order": order, "content": formatted_section}]}
        
    except Exception as e:
        logger.error(f"[WRITER] Error writing section {section.heading}: {e}")
        # Return error placeholder so the article can still be assembled
        error_content = f"## {section.heading}\n\n(Error writing this section: {e})\n\n"
        return {"sections_content": [{"order": order, "content": error_content}]}
