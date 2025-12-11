"""
Logging configuration for ANCA with token-efficient output.
Reduces verbosity while keeping critical information.
"""
import logging
import sys
from pathlib import Path


class TokenEfficientFormatter(logging.Formatter):
    """Formatter that abbreviates verbose messages to reduce token usage."""
    
    # Messages to completely suppress
    SUPPRESS_PATTERNS = [
        "Wrapper: Completed Call",
        "POST Request Sent",
        "HTTP Request:",
        "ANSI escape code",
        "Starting scraping...",
        "Content scraped",
    ]
    
    # Messages to abbreviate
    ABBREVIATIONS = {
        "Successfully parsed robots.txt for": "✓ robots.txt:",
        "Waiting ": "⏳ ",
        "Starting scrape for": "🔍",
        "Successfully wrote": "✅",
        "Ingested": "📥",
        "Retrieved": "📤",
        "Creating": "🔧",
        "ChromaDB initialized": "💾",
    }
    
    def format(self, record):
        # Suppress noisy messages
        for pattern in self.SUPPRESS_PATTERNS:
            if pattern in record.getMessage():
                return ""  # Empty string won't be printed
        
        # Abbreviate common messages
        msg = record.getMessage()
        for full, abbrev in self.ABBREVIATIONS.items():
            if full in msg:
                msg = msg.replace(full, abbrev)
        
        # Format: [TIME] LEVEL: message (no module names for brevity)
        return f"[{self.formatTime(record, '%H:%M:%S')}] {record.levelname[0]}: {msg}"


def setup_token_efficient_logging(log_dir: Path, session_name: str = "anca"):
    """
    Setup logging that's readable but token-efficient.
    
    Args:
        log_dir: Directory for log files
        session_name: Name for this logging session
    """
    from datetime import datetime
    from logging.handlers import RotatingFileHandler
    
    # Ensure log directory exists
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create session log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{session_name}_{timestamp}.log"
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    
    # File handler (detailed)
    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,  # Keep only 3 old logs
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(TokenEfficientFormatter())
    
    # Console handler (even more condensed)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(TokenEfficientFormatter())
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce verbosity of chatty libraries
    logging.getLogger('litellm').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('crewai').setLevel(logging.WARNING)  # Reduce CrewAI noise
    
    print(f"📝 Logging to: {log_file}")
    return log_file


def log_milestone(message: str, level: str = "INFO"):
    """
    Log a milestone event with emphasis.
    Use this for key events you want to find quickly in logs.
    """
    logger = logging.getLogger("MILESTONE")
    symbols = {"INFO": "🎯", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}
    symbol = symbols.get(level, "📌")
    
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"\n{'='*60}\n{symbol} {message}\n{'='*60}")
