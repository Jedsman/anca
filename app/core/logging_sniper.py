import logging
import sys
from pathlib import Path
from app.core.config import settings # Re-use base settings for logs_dir

def get_sniper_logger(name: str) -> logging.Logger:
    """
    Get a dedicated logger for the Sniper agent that logs to both console and file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent adding handlers multiple times if get_logger is called repeatedly
    if logger.hasHandlers():
        return logger
        
    # Ensure logs directory exists
    log_dir = settings.logs_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "sniper.log"
    
    # File Handler
    file_handler = logging.FileHandler(str(log_file), encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
