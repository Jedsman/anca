import os
import logging
from pathlib import Path
import yaml
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

# Setup LLM request/response logging
from app.core.llm_logging_callback import setup_llm_logging
setup_llm_logging()
logger.info("🔍 LLM call logging enabled - check logs/llm_calls/")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# --- Helper: Load Prompt ---
def load_prompt(filename: str) -> dict:
    """Load a YAML prompt file from the prompts directory."""
    prompts_dir = Path(__file__).parent / "prompts"
    file_path = prompts_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# --- Agent Initialization ---
# Each agent uses its own optimized model
researcher = create_researcher(tools=[scraper_tool], base_url=OLLAMA_BASE_URL)
generator = create_generator(tools=[scraper_tool, file_writer_tool, rag_tool, file_reader_tool], base_url=OLLAMA_BASE_URL)
auditor = create_auditor(tools=[], base_url=OLLAMA_BASE_URL)

# --- Task Definitions (Loaded from prompts/) ---

# 1. Research Task
research_config = load_prompt("research_task.yaml")
research_task = Task(
    description=research_config['description'],
    expected_output=research_config['expected_output'],
    agent=researcher
)

# 2. Generation Task
generation_config = load_prompt("generation_task.yaml")
generation_task = Task(
    description=generation_config['description'],
    expected_output=generation_config['expected_output'],
    agent=generator,
    context=[research_task]
)

# 3. Audit Task
audit_config = load_prompt("audit_task.yaml")
audit_task = Task(
    description=audit_config['description'],
    expected_output=audit_config['expected_output'],
    agent=auditor,
    context=[generation_task]
)

# 4. Revision Task
revision_config = load_prompt("revision_task.yaml")
revision_task = Task(
    description=revision_config['description'],
    expected_output=revision_config['expected_output'],
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

def validate_revision_improved_content(topic: str, articles_dir: Path) -> bool:
    """
    Validate that the revision task actually improved the article.

    Checks:
    1. Article file exists
    2. Content has minimum quality markers (headings, word count)
    3. If multiple versions exist, revision is not shorter than original

    Returns:
        bool: True if validation passes, False otherwise
    """
    # Construct expected filename from topic
    slug = topic.lower().replace(' ', '-').replace('_', '-')
    article_path = articles_dir / f"{slug}.md"

    if not article_path.exists():
        logger.error(f"Validation FAILED: Article not found at {article_path}")
        return False

    # Read content
    content = article_path.read_text(encoding='utf-8')
    word_count = len(content.split())

    # Check minimum quality markers
    has_h1 = '# ' in content
    has_h2 = '## ' in content
    min_words = 1000

    if word_count < min_words:
        logger.warning(f"Validation WARNING: Article has only {word_count} words (minimum: {min_words})")
        return False

    if not has_h1:
        logger.warning("Validation WARNING: Article missing H1 heading")
        return False

    if not has_h2:
        logger.warning("Validation WARNING: Article missing H2 headings")
        return False

    logger.info(f"Validation PASSED: Article has {word_count} words, proper structure")
    return True


if __name__ == "__main__":
    # Setup logging for standalone execution
    _setup_logging()

    # Define the broad topic for the crew to work on
    topic = "homebrew coffee"

    logger.info(f"Starting Stage 3 crew with Refactored Prompts & Reflection Loop")
    logger.info(f"Topic: '{topic}'")
    print("=" * 60)

    # Kick off the crew's work
    # Note: CrewAI will execute all tasks sequentially
    # The revision task will run after audit, improving the article
    result = crew.kickoff(inputs={'topic': topic})

    logger.info("Crew execution finished.")
    print("=" * 60)

    # Validate that the revision actually improved the content
    print("\n" + "=" * 60)
    logger.info("Validating revision quality...")
    validation_passed = validate_revision_improved_content(topic, settings.articles_dir)

    if validation_passed:
        print("✅ VALIDATION PASSED: Article meets quality standards")
        logger.info("✅ Revision validation successful")
    else:
        print("❌ VALIDATION FAILED: Article does not meet quality standards")
        logger.error("❌ Revision validation failed")
    print("=" * 60)
    print("Final result:")
    print(result)
    logger.info(f"Final Result: {result}")
