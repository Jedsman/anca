
import os
import logging
from typing import TypedDict, List, Annotated
from typing_extensions import NotRequired

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages

from app.core.config import settings
from app.core.langchain_logging_callback import LangChainLoggingHandler

# --- Tools Imports ---
# We need to adapt tools to be bindable functions or Pydantic tools
from langchain_core.tools import tool
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool
from tools.rag_tool import RAGTool
from tools.file_reader_tool import FileReaderTool

# Setup Logger
logger = logging.getLogger(__name__)

# --- 1. Define State ---
import yaml
from pathlib import Path

def load_prompt(filename: str) -> dict:
    """Load a YAML prompt file from the prompts directory."""
    prompts_dir = Path(__file__).parent / "prompts"
    file_path = prompts_dir / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Load prompts
audit_config = load_prompt("audit_task.yaml")
generation_config = load_prompt("generation_task.yaml")
research_config = load_prompt("research_task.yaml")
revision_config = load_prompt("revision_task.yaml")
critique_config = load_prompt("critique_task.yaml")
expansion_config = load_prompt("expansion_task.yaml")

class AgentState(TypedDict):
    topic: str
    research_data: List[str]  # Just URLs for now, or summaries
    content_draft: str
    audit_feedback: str
    revision_count: int
    critique_count: int  # Critique loop counter
    target_length: int   # Minimum word count target (default 1800)
    filename: NotRequired[str]  # Filename of the generated article
    messages: Annotated[List[BaseMessage], add_messages]

# --- 2. Setup Tools ---
# We wrap CrewAI tools into LangChain compatible tools if needed.
# Since we want NATIVE tool calling, we should ideally define them as functions with Pydantic args.

# Initialize existing tools
scraper = ScraperTool()
file_writer = FileWriterTool()
rag = RAGTool()
file_reader = FileReaderTool()

# We need to expose the underlying run method as a tool for LangChain to bind to
# For simplicity in this v1 migration, we will create simple wrapper functions annotated with @tool
# equal to the logic we want.

@tool
def scrape_website(url: str):
    """Scrape content from a website URL."""
    return scraper._run(url)

@tool
def save_article(filename: str, content: str):
    """Save the full markdown article to a file."""
    if not content or len(content) < 50:
        return "Error: Content too short to save."
    return file_writer._run(filename=filename, content=content)

@tool
def ingest_content(url: str):
    """Ingest a URL into the RAG knowledge base."""
    return rag._run(action="ingest", url=url)

@tool
def retrieve_context(query: str):
    """Retrieve relevant context from the knowledge base."""
    return rag._run(action="retrieve", query=query)

# Group tools by agent
research_tools = [scrape_website]
generator_tools = [save_article, ingest_content, retrieve_context]
# Auditor just gives feedback, no tools needed usually, maybe reader?
auditor_tools = [] 

# --- 3. Setup Nodes from Modules ---
from agents.researcher import create_researcher_node
from agents.generator import create_generator_node
from agents.auditor import create_auditor_node
from agents.reviser import create_seo_reviser_node
from agents.critique import create_critique_node

# Create the agent runnables
research_agent = create_researcher_node()
generator_agent = create_generator_node()
auditor_agent = create_auditor_node()
reviser_agent = create_seo_reviser_node()
critique_agent = create_critique_node()

# --- 4. Define Node Logic (Wrapping agents to handle State) ---

def researcher_node_wrapper(state: AgentState):
    logger.info("--- Researcher Agent ---")
    messages = state['messages']
    if not messages:
        # Use research task description
        prompt = research_config['description'].format(topic=state['topic'])
        messages = [HumanMessage(content=prompt)]

    # Limit agent's internal tool-calling loop (search + scrape 4 URLs + ingest 4 = ~20 calls max)
    result = research_agent.invoke({"messages": messages}, config={"recursion_limit": 30})
    return {"messages": result["messages"]}

def generator_node_wrapper(state: AgentState):
    logger.info("--- Generator Agent ---")
    
    critique_count = state.get('critique_count', 0)
    
    if critique_count > 0:
        # EXPANSION MODE
        logger.info(f"Refining content (Attempt {critique_count}). Switching to Expansion Prompt.")
        
        # Get last message which should be the critique feedback
        feedback = state['messages'][-1].content
        filename = state.get('filename', 'unknown.md')
        target_length = state.get('target_length', 1800)
        
        instruction = expansion_config['description'].format(
            filename=filename,
            feedback=feedback,
            target_length=target_length
        )
        
        logger.info(f"Generator using filename: {filename}")
        
    else:
        # INITIAL GENERATION MODE
        # Get the last message from the researcher
        last_message = state['messages'][-1].content
        
        # [FIX] Enforce filename consistency
        # If filename is not in state yet, generate it from topic
        filename = state.get('filename')
        if not filename:
            import re
            slug = state['topic'].lower().replace(' ', '-').replace('_', '-')
            # Remove non-alphanumeric chars (except dash)
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            filename = f"{slug}.md"
            logger.info(f"Assigned mandated filename: {filename}")
    
        # Use generation task description
        instruction = generation_config['description'].format(
            topic=state['topic'],
            filename=filename
        )
        # Append context from researcher
        instruction += f"\n\nCONTEXT FROM RESEARCHER:\n{last_message}"
    
    # Debug print
    # print(f"\n\n=== DEBUG: GENERATOR PROMPT ===\n{instruction[:200]}...\n==============================\n")

    # Limit agent's internal tool-calling loop (retrieve ~5x + save = ~15 calls max)
    result = generator_agent.invoke({"messages": [HumanMessage(content=instruction)]}, config={"recursion_limit": 25})

    # Extract filename from tool calls if save_article was called
    # Don't reset filename - preserve the pre-calculated one from above
    extracted_filename = None
    for msg in result["messages"]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == 'save_article':
                    extracted_filename = tool_call.get('args', {}).get('filename')
                    logger.info(f"Extracted filename from generator: {extracted_filename}")
                    break

    # Use extracted filename if available, otherwise keep the pre-calculated one
    final_filename = extracted_filename if extracted_filename else filename
    logger.info(f"Final filename for state: {final_filename}")

    return {"messages": result["messages"], "filename": final_filename}

def auditor_node_wrapper(state: AgentState):
    logger.info("--- Auditor Agent ---")

    # Use audit task description
    instruction = audit_config['description'].format(topic=state['topic'])

    # Add filename information if available
    if state.get('filename'):
        instruction += f"\n\n**ARTICLE FILENAME TO AUDIT:** `{state['filename']}`\n"
        instruction += f"Use the `read_article_file` tool with filename=\"{state['filename']}\" to read the article."
        logger.info(f"Auditor will read file: {state['filename']}")

    # Limit agent's internal tool-calling loop (read + analyze = ~5 calls max)
    result = auditor_agent.invoke({"messages": [HumanMessage(content=instruction)]}, config={"recursion_limit": 10})
    return {"messages": result["messages"]}

def reviser_node_wrapper(state: AgentState):
    logger.info("--- Reviser Agent ---")

    # Increment revision count
    revision_count = state.get('revision_count', 0) + 1
    logger.info(f"Revision attempt {revision_count}/3")

    # Get the audit feedback from the last message
    audit_feedback = state['messages'][-1].content

    # Use revision task description
    instruction = revision_config['description'].format(topic=state['topic'])

    # Add filename and audit feedback context
    if state.get('filename'):
        instruction += f"\n\n**ARTICLE FILENAME:** `{state['filename']}`\n"
        instruction += f"Use the `read_file` tool with filename=\"{state['filename']}\" to read the current article.\n"
        logger.info(f"Reviser will revise file: {state['filename']}")

    instruction += f"\n\n**AUDIT FEEDBACK FROM PREVIOUS STEP:**\n{audit_feedback}\n"
    instruction += f"\n**REVISION ATTEMPT:** {revision_count}/3\n"
    instruction += "\nImplement ALL required changes to achieve a 10/10 score."

    # Use the dedicated reviser agent
    # Limit agent's internal tool-calling loop (read + revise + save = ~8 calls max)
    result = reviser_agent.invoke({"messages": [HumanMessage(content=instruction)]}, config={"recursion_limit": 15})

    # Extract filename from tool calls if save_article was called (in case it changed or was re-saved)
    filename = state.get('filename')
    for msg in result["messages"]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == 'save_article':
                    new_filename = tool_call.get('args', {}).get('filename')
                    if new_filename:
                        filename = new_filename
                        logger.info(f"Extracted updated filename from reviser: {filename}")
                    break

    return {"messages": result["messages"], "revision_count": revision_count, "filename": filename}

def critique_node_wrapper(state: AgentState):
    """QA Critique agent - evaluates article quality and length."""
    logger.info("--- Critique Agent ---")
    
    # Increment critique count
    critique_count = state.get('critique_count', 0) + 1
    target_length = state.get('target_length', 1800)
    logger.info(f"Critique evaluation {critique_count}/3 (target: {target_length} words)")
    
    # Use critique task description
    instruction = critique_config['description'].format(
        topic=state['topic'],
        target_length=target_length
    )
    
    # Add filename information
    if state.get('filename'):
        instruction += f"\n\n**ARTICLE FILENAME:** `{state['filename']}`\n"
        instruction += f"Use the `read_file` tool with filename=\"{state['filename']}\" to read the article."
        logger.info(f"Critique will evaluate file: {state['filename']}")
    
    # Limit agent's internal tool-calling loop (read + evaluate = ~5 calls max)
    result = critique_agent.invoke({"messages": [HumanMessage(content=instruction)]}, config={"recursion_limit": 10})
    
    return {"messages": result["messages"], "critique_count": critique_count}

def should_continue_critique(state: AgentState) -> str:
    """
    Decide whether article passes QA critique or needs expansion.
    
    Returns:
        "auditor" - PASS, proceed to SEO audit
        "generator" - FAIL, send back to generator for expansion
        "end" - Max critique attempts reached
    """
    critique_count = state.get('critique_count', 0)
    max_critiques = 3
    
    # Check if we've hit max critiques
    if critique_count >= max_critiques:
        logger.info(f"Max critique attempts ({max_critiques}) reached. Proceeding to audit anyway.")
        return "auditor"
    
    # Try to extract PASS/FAIL status from the last critique message
    messages = state.get('messages', [])
    if messages:
        for msg in reversed(messages):
            content = msg.content if hasattr(msg, 'content') else str(msg)
            # Check for PASS/FAIL status
            import re
            status_match = re.search(r'\*\*Status:\*\*\s*(PASS|FAIL)', content, re.IGNORECASE)
            if status_match:
                status = status_match.group(1).upper()
                logger.info(f"Detected critique status: {status}")
                if status == "PASS":
                    logger.info("Critique PASSED. Proceeding to SEO audit.")
                    return "auditor"
                else:
                    logger.info(f"Critique FAILED. Sending back to generator (attempt {critique_count}/{max_critiques}).")
                    return "generator"
    
    # Default: if can't parse, proceed to audit
    logger.warning("Could not parse critique status. Proceeding to audit.")
    return "auditor"

def should_continue_revising(state: AgentState) -> str:
    """
    Decide whether to continue the revision loop or end.

    Returns:
        "auditor" - Continue loop (re-audit the revised article)
        "end" - Stop loop (max revisions reached or quality sufficient)
    """
    revision_count = state.get('revision_count', 0)
    max_revisions = 3

    # Check if we've hit max revisions
    if revision_count >= max_revisions:
        logger.info(f"Max revisions ({max_revisions}) reached. Ending workflow.")
        return "end"

    # Try to extract quality score from the last auditor message
    # Look for patterns like "Quality Score: 8/10" or "Score: 8/10"
    messages = state.get('messages', [])
    if messages:
        # Find the most recent auditor message
        for msg in reversed(messages):
            content = msg.content if hasattr(msg, 'content') else str(msg)
            # Simple pattern matching for score
            import re
            score_match = re.search(r'(?:Quality Score|Score):\s*(\d+)/10', content, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
                logger.info(f"Detected quality score: {score}/10")
                if score >= 9:  # Quality threshold
                    logger.info(f"Quality threshold met ({score}/10 >= 9/10). Ending workflow.")
                    return "end"

    # Continue revising
    logger.info(f"Continuing revision loop (attempt {revision_count}/{max_revisions})")
    return "auditor"


# --- 5. Build Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher_node_wrapper)
workflow.add_node("generator", generator_node_wrapper)
workflow.add_node("critique", critique_node_wrapper)
workflow.add_node("auditor", auditor_node_wrapper)
workflow.add_node("reviser", reviser_node_wrapper)

# Flow: research → generate → critique → (conditional) → audit → revise → (conditional)
workflow.add_edge(START, "researcher")
workflow.add_edge("researcher", "generator")
workflow.add_edge("generator", "critique")

# Conditional routing after critique:
# - PASS → proceed to SEO audit
# - FAIL → send back to generator for expansion (up to 3 attempts)
workflow.add_conditional_edges(
    "critique",
    should_continue_critique,
    {
        "auditor": "auditor",    # PASS: proceed to SEO audit
        "generator": "generator", # FAIL: expand content
    }
)

workflow.add_edge("auditor", "reviser")

# Conditional routing after revision:
# - If quality good OR max revisions reached → END
# - Otherwise → back to auditor for re-audit
workflow.add_conditional_edges(
    "reviser",
    should_continue_revising,
    {
        "auditor": "auditor",  # Continue loop: revise → audit → revise
        "end": END  # Exit loop
    }
)

app = workflow.compile()

def validate_revision_quality(topic: str, filename: str = None) -> bool:
    """
    Validate that the revision improved the article quality.

    Checks:
    1. Article file exists
    2. Content has minimum quality markers (headings, word count)
    3. Meets SEO quality standards

    Returns:
        bool: True if validation passes, False otherwise
    """
    from pathlib import Path
    from app.core.config import settings

    # Construct expected filename if not provided
    if not filename:
        slug = topic.lower().replace(' ', '-').replace('_', '-')
        filename = f"{slug}.md"

    article_path = settings.articles_dir / filename

    if not article_path.exists():
        logger.error(f"❌ Validation FAILED: Article not found at {article_path}")
        return False


    from tools.word_count_tool import count_markdown_words

    # Read content
    content = article_path.read_text(encoding='utf-8')
    word_count = count_markdown_words(content)

    # Check quality markers
    has_h1 = '# ' in content
    has_h2 = '## ' in content

    # SEO content length standards
    min_words = 1500  # Minimum for SEO
    optimal_min = 1800  # Optimal range start
    optimal_max = 2500  # Optimal range end

    validation_passed = True
    issues = []
    warnings = []

    # Critical validation (must pass)
    if word_count < min_words:
        issues.append(f"Article has only {word_count} words (minimum: {min_words})")
        validation_passed = False

    if not has_h1:
        issues.append("Article missing H1 heading")
        validation_passed = False

    if not has_h2:
        issues.append("Article missing H2 headings")
        validation_passed = False

    # Optimal range warnings (informational)
    if validation_passed:
        if word_count < optimal_min:
            warnings.append(f"Article is {word_count} words (optimal: {optimal_min}-{optimal_max})")
        elif word_count > optimal_max:
            warnings.append(f"Article is {word_count} words (consider splitting if too long)")

    if validation_passed:
        if warnings:
            logger.info(f"[PASS] Validation PASSED: Article has {word_count} words, proper structure")
            logger.info(f"[INFO] Optimization suggestion: {'; '.join(warnings)}")
        else:
            logger.info(f"[PASS] Validation PASSED: Article has {word_count} words (optimal range), proper structure")
        return True
    else:
        logger.warning(f"[FAIL] Validation FAILED: {', '.join(issues)}")
        return False


# Configure logging ONLY if running as main script (not imported)
def _setup_logging():
    """Setup logging for standalone execution with rotation"""
    from logging.handlers import RotatingFileHandler
    import logging

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Import custom formatter
    from app.core.logging_utils import AnsiStrippingFormatter, get_session_log_file
    
    # Get session log file
    log_file = get_session_log_file("anca_graph", settings.logs_dir)
    
    file_formatter = AnsiStrippingFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Session-based File Handler
    file_handler = logging.FileHandler(
        str(log_file),
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(settings.log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.log_level)

    # Setup Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger.info(f"[LOG] Logs will be written to: {log_file}")


# --- 6. Execution ---
if __name__ == "__main__":
    import argparse
    from app.core.config import settings

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run ANCA content generation workflow")
    parser.add_argument("--topic", type=str, default="how to brew coffee at home", help="Topic to generate content about")
    parser.add_argument("--clear-rag", action="store_true", help="Clear RAG database before starting (recommended for new topics)")
    args = parser.parse_args()

    # Setup logging
    _setup_logging()

    topic = args.topic

    # Optionally clear RAG database for fresh start
    if args.clear_rag:
        logger.info("Clearing RAG database for fresh start...")
        rag.clear_collection()
        print("[INFO] RAG database cleared")

    print(f"Starting LangGraph workflow for topic: {topic}")
    print("Workflow: Researcher -> Generator -> Critique (loop) -> Auditor -> SEO Reviser (loop)")
    print("=" * 60)

    result = app.invoke(
        {
            "topic": topic,
            "messages": [],
            "revision_count": 0,    # Initialize revision counter
            "critique_count": 0,    # Initialize critique counter
            "target_length": 1800,  # Minimum word count target
        },
        config={"recursion_limit": 300}  # High limit for 5 agents + dual revision loops
    )

    print("\n\n----------------- FINAL OUTPUT -----------------\n")
    print("\n\n----------------- FINAL OUTPUT -----------------\n")

    # Show revision statistics
    revision_count = result.get('revision_count', 0)
    print(f"[Stats] Revisions completed: {revision_count}/3")
    print("=" * 60)

    for m in result['messages']:
        print(f"[{m.type}]: {m.content}")
        if hasattr(m, 'tool_calls') and m.tool_calls:
            print(f"   >>> TOOL CALLS: {m.tool_calls}")

    # Validate the revision quality
    print("\n" + "=" * 60)
    logger.info("Validating revision quality...")
    filename = result.get('filename')
    validation_passed = validate_revision_quality(topic, filename)

    if validation_passed:
        print(f"[PASS] VALIDATION PASSED: Article meets quality standards after {revision_count} revision(s)")
        logger.info("[PASS] Revision validation successful")
    else:
        print(f"[WARN] VALIDATION WARNING: Article may need further improvements (after {revision_count} revision(s))")
        logger.warning("[WARN] Revision validation had warnings")
    print("=" * 60)
