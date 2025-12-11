
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

class AgentState(TypedDict):
    topic: str
    research_data: List[str]  # Just URLs for now, or summaries
    content_draft: str
    audit_feedback: str
    revision_count: int
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
from agents.reviser import create_reviser_node

# Create the agent runnables
research_agent = create_researcher_node()
generator_agent = create_generator_node()
auditor_agent = create_auditor_node()
reviser_agent = create_reviser_node()

# --- 4. Define Node Logic (Wrapping agents to handle State) ---

def researcher_node_wrapper(state: AgentState):
    logger.info("--- Researcher Agent ---")
    messages = state['messages']
    if not messages:
        # Use research task description
        prompt = research_config['description'].format(topic=state['topic'])
        messages = [HumanMessage(content=prompt)]
    
    result = research_agent.invoke({"messages": messages})
    return {"messages": result["messages"]}

def generator_node_wrapper(state: AgentState):
    logger.info("--- Generator Agent ---")
    # Get the last message from the researcher
    last_message = state['messages'][-1].content

    # Use generation task description
    instruction = generation_config['description'].format(topic=state['topic'])
    # Append context from researcher
    instruction += f"\n\nCONTEXT FROM RESEARCHER:\n{last_message}"

    print(f"\n\n=== DEBUG: GENERATOR PROMPT ({len(instruction)} chars) ===\n{instruction}\n==========================================\n")

    result = generator_agent.invoke({"messages": [HumanMessage(content=instruction)]})

    # Extract filename from tool calls if save_article was called
    filename = None
    for msg in result["messages"]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == 'save_article':
                    filename = tool_call.get('args', {}).get('filename')
                    logger.info(f"Extracted filename from generator: {filename}")
                    break

    return {"messages": result["messages"], "filename": filename}

def auditor_node_wrapper(state: AgentState):
    logger.info("--- Auditor Agent ---")

    # Use audit task description
    instruction = audit_config['description'].format(topic=state['topic'])

    # Add filename information if available
    if state.get('filename'):
        instruction += f"\n\n**ARTICLE FILENAME TO AUDIT:** `{state['filename']}`\n"
        instruction += f"Use the `read_article_file` tool with filename=\"{state['filename']}\" to read the article."
        logger.info(f"Auditor will read file: {state['filename']}")

    result = auditor_agent.invoke({"messages": [HumanMessage(content=instruction)]})
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
    result = reviser_agent.invoke({"messages": [HumanMessage(content=instruction)]})

    return {"messages": result["messages"], "revision_count": revision_count}

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
workflow.add_node("auditor", auditor_node_wrapper)
workflow.add_node("reviser", reviser_node_wrapper)

# Linear flow: research → generate → audit → revise
workflow.add_edge(START, "researcher")
workflow.add_edge("researcher", "generator")
workflow.add_edge("generator", "auditor")
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

    # Read content
    content = article_path.read_text(encoding='utf-8')
    word_count = len(content.split())

    # Check minimum quality markers
    has_h1 = '# ' in content
    has_h2 = '## ' in content
    min_words = 1000

    validation_passed = True
    issues = []

    if word_count < min_words:
        issues.append(f"Article has only {word_count} words (minimum: {min_words})")
        validation_passed = False

    if not has_h1:
        issues.append("Article missing H1 heading")
        validation_passed = False

    if not has_h2:
        issues.append("Article missing H2 headings")
        validation_passed = False

    if validation_passed:
        logger.info(f"✅ Validation PASSED: Article has {word_count} words, proper structure")
        return True
    else:
        logger.warning(f"⚠️ Validation WARNING: {', '.join(issues)}")
        return False


# --- 6. Execution ---
if __name__ == "__main__":
    from app.core.config import settings

    # Setup logging manually since we are bypassing main app
    logging.basicConfig(level=logging.INFO)
    # Available logging levels: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET

    topic = "homebrew coffee"
    print(f"Starting LangGraph workflow for topic: {topic}")
    print("Workflow: Researcher → Generator → Auditor → Reviser (loop up to 3x)")
    print("=" * 60)

    result = app.invoke({
        "topic": topic,
        "messages": [],
        "revision_count": 0  # Initialize revision counter
    })

    print("\n\n----------------- FINAL OUTPUT -----------------\n")
    print("\n\n----------------- FINAL OUTPUT -----------------\n")

    # Show revision statistics
    revision_count = result.get('revision_count', 0)
    print(f"📊 Revisions completed: {revision_count}/3")
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
        print(f"✅ VALIDATION PASSED: Article meets quality standards after {revision_count} revision(s)")
        logger.info("✅ Revision validation successful")
    else:
        print(f"⚠️ VALIDATION WARNING: Article may need further improvements (after {revision_count} revision(s))")
        logger.warning("⚠️ Revision validation had warnings")
    print("=" * 60)
