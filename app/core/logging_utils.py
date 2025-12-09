import logging
import sys
import re

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
             # Avoid logging empty lines that result from rstrip/split
             if line.strip():
                self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

class AnsiStrippingFormatter(logging.Formatter):
    """
    Formatter that strips ANSI escape codes from the log message.
    """
    ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def format(self, record):
        # Strip ANSI codes from the message
        if record.msg and isinstance(record.msg, str):
            record.msg = self.ANSI_RE.sub('', record.msg)
        return super().format(record)

def get_session_log_file(base_name: str, logs_dir: "pathlib.Path", max_files: int = 10) -> "pathlib.Path":
    """
    Generate a timestamped log filename for the current session and clean up old logs.
    
    Args:
        base_name: Base name for the log file (e.g., 'anca')
        logs_dir: Directory where logs are stored
        max_files: Maximum number of recent log files to keep for this base_name
        
    Returns:
        Path to the new log file
    """
    from datetime import datetime
    import glob
    import os
    
    # ensure logs_dir exists
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)

    # Generate new filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = logs_dir / f"{base_name}_{timestamp}.log"
    
    # Cleanup old logs
    try:
        # Find all files matching the pattern
        pattern = str(logs_dir / f"{base_name}_*.log")
        files = glob.glob(pattern)
        
        # Sort by modification time (newest last)
        files.sort(key=os.path.getmtime)
        
        # Remove old files if we have more than max_files
        while len(files) >= max_files:
            os.remove(files[0])
            files.pop(0)
            
    except Exception as e:
        print(f"Warning: Failed to cleanup old logs: {e}")
        
    return log_file
