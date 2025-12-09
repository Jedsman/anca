import os
import logging
from crewai import Crew, Process, Task
from dotenv import load_dotenv

from app.core.config import settings

# Load environment variables from .env file
load_dotenv()

# Configure logging ONLY if running as main script (not imported)
# When imported by API, app.main handles logging setup
def _setup_logging():
    """Setup logging for standalone execution with rotation"""
    from logging.handlers import RotatingFileHandler

    # settings.logs_dir.mkdir(parents=True, exist_ok=True)
    # log_file = settings.logs_dir / "anca_1.log"  # Use different log file for UV runs

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Import custom formatter
    from app.core.logging_utils import AnsiStrippingFormatter, get_session_log_file
    
    # Get session log file
    log_file = get_session_log_file("anca_cli", settings.logs_dir)
    
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

    # Setup Root Logger - explicitly add handlers instead of using basicConfig
    # This ensures handlers are added even if logging was already initialized
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Redirect stdout to logger to capture CrewAI output
    from app.core.logging_utils import StreamToLogger
    import sys
    sys.stdout = StreamToLogger(root_logger, logging.INFO)


logger = logging.getLogger(__name__)

# Import tools
from tools.scraper_tool import ScraperTool
from tools.file_writer_tool import FileWriterTool
from tools.rag_tool import RAGTool
from tools.file_reader_tool import FileReaderTool

# Import agent factories
from agents import create_researcher, create_generator, create_auditor

# Initialize tools
scraper_tool = ScraperTool()
file_writer_tool = FileWriterTool()
rag_tool = RAGTool()
file_reader_tool = FileReaderTool()

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# --- Agent Initialization ---
# Each agent uses its own optimized model

researcher = create_researcher(tools=[scraper_tool], base_url=OLLAMA_BASE_URL)
generator = create_generator(tools=[scraper_tool, file_writer_tool, rag_tool, file_reader_tool], base_url=OLLAMA_BASE_URL)
auditor = create_auditor(tools=[], base_url=OLLAMA_BASE_URL)

# --- Task Definitions ---

# 1. Research Task
research_task = Task(
    description=(
        "Analyze the given topic: '{topic}'. Find 3-5 high-ranking articles "
        "from DIFFERENT domains/websites related to this topic. "
        "Focus on:\n"
        "1. A specific, low-competition, long-tail keyword\n"
        "2. Diverse, authoritative sources (avoid using same domain twice)\n"
        "3. High-quality content that ranks well\n\n"
        "The goal is to gather multiple perspectives for a comprehensive article."
    ),
    expected_output=(
        "A report containing:\n"
        "1. The chosen long-tail keyword/topic\n"
        "2. A list of 3-5 URLs from DIFFERENT domains\n"
        "3. Brief note on why each source is valuable"
    ),
    agent=researcher
)

# 2. Generation Task (with RAG and multiple sources)
generation_task = Task(
    description=(
        "Using the keyword and source URLs provided by the Market Researcher:\n"
        "1. Scrape ALL the provided URLs using the scraper tool\n"
        "2. Ingest each URL into RAG using the rag_tool (action='ingest', url='...')\n"
        "3. Use rag_tool (action='retrieve', query='...') to find relevant details\n"
        "4. Synthesize a comprehensive, well-structured blog post that:\n"
        "   - Combines insights from multiple sources\n"
        "   - Provides diverse perspectives\n"
        "   - Is original and not just copied content\n"
        "   - Covers the topic in depth\n"
        "5. Save to markdown file using the FileWriterTool. \n"
        "   IMPORTANT: The filename MUST be the topic converted to a slug (e.g., 'home-coffee').\n"
        "   The system will automatically add the .md extension.\n"
        "   DO NOT use generic names like 'article' or 'slugified_topic'."
    ),
    expected_output=(
        "A confirmation message EXACTLY in this format:\n"
        "Article written to: [FILENAME]\n"
        "Sources used: [COUNT]"
    ),
    agent=generator,
    context=[research_task]
)

# 3. Audit Task (Quality Check)
audit_task = Task(
    description=(
        "Review the generated blog post for SEO quality and E-E-A-T compliance. "
        "Evaluate:\n"
        "1. SEO: Keyword usage, headings structure, content length\n"
        "2. E-E-A-T: Experience, Expertise, Authoritativeness, Trustworthiness\n"
        "3. Readability: Clear structure, engaging writing\n"
        "4. Completeness: Topic coverage depth\n\n"
        "Provide specific, actionable feedback. "
        "IMPORTANT: Start your response with a quality score (1-10) on the first line."
    ),
    expected_output=(
        "A detailed quality report starting with:\n"
        "Quality Score: X/10\n\n"
        "Then include:\n"
        "1. Specific strengths\n"
        "2. Areas for improvement\n"
        "3. Actionable recommendations"
    ),
    agent=auditor,
    context=[generation_task]
)

# 4. Revision Task (Improve based on feedback)
revision_task = Task(
    description=(
        "The SEO Auditor has reviewed the article and provided feedback. "
        "Your job is to improve the article based on this feedback.\n\n"
        "Steps:\n"
        "1. LOOK at the 'Article written to: [FILENAME]' output from the Generation Task above.\n"
        "2. Use the FileReaderTool to read that EXACT filename. \n"
        "   IMPORTANT: Provide ONLY the filename (e.g., 'topic.md'). Do NOT include 'articles/'.\n"
        "3. Review the Auditor's recommendations carefully\n"
        "4. Identify the key improvements needed\n"
        "5. Rewrite the article incorporating all feedback\n"
        "6. Use the FileWriterTool to save the improved version with the SAME filename\n\n"
        "Focus on:\n"
        "- Addressing all identified weaknesses\n"
        "- Maintaining existing strengths\n"
        "- Improving SEO and E-E-A-T compliance\n"
        "- Enhancing readability and structure"
    ),
    expected_output=(
        "Confirmation that the revised article has been saved, "
        "listing the main improvements made."
    ),
    agent=generator,
    context=[generation_task, audit_task]
)

# --- Crew Definition with Iteration ---

# Create the crew with sequential process and reflection
crew = Crew(
    agents=[researcher, generator, auditor],
    tasks=[research_task, generation_task, audit_task, revision_task],
    process=Process.sequential,
    verbose=True,
    max_rpm=10  # Rate limit to avoid overwhelming local LLMs
)

# --- Execute the Crew with Revision Loop ---

if __name__ == "__main__":
    # Setup logging for standalone execution
    _setup_logging()

    # Define the broad topic for the crew to work on
    topic = "homebrew coffee"

    logger.info(f"Starting Stage 3 crew with RAG, SEO Auditor, and Revision Loop")
    logger.info(f"Topic: '{topic}'")
    print("=" * 60)

    # Kick off the crew's work
    # Note: CrewAI will execute all tasks sequentially
    # The revision task will run after audit, improving the article
    result = crew.kickoff(inputs={'topic': topic})

    logger.info("Crew execution finished.")
    print("=" * 60)
    print("Final result:")
    print(result)
    logger.info(f"Final Result: {result}")
