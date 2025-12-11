"""
Tool call interceptor for debugging LLM tool usage.
Logs all tool calls with their arguments in a readable format.
"""
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ToolCallLogger:
    """Logs all tool calls for debugging and analysis."""
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path("logs/tool_calls")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._log_files = {}  # Cache of tool_name -> file_path
        
    def _get_log_file(self, tool_name: str) -> Path:
        """Get or create log file for a specific tool."""
        if tool_name not in self._log_files:
            # Create separate file per tool: FileWriterTool_20251209_232434.jsonl
            safe_tool_name = tool_name.replace(" ", "_")
            log_file = self.log_dir / f"{safe_tool_name}_{self.session_timestamp}.jsonl"
            self._log_files[tool_name] = log_file
            logger.info(f"📝 {tool_name} calls will be logged to: {log_file.name}")
        return self._log_files[tool_name]
        
    def log_call(self, tool_name: str, arguments: Dict[str, Any], result: Any = None, error: str = None):
        """
        Log a tool call in both human-readable and machine-readable formats.
        
        Args:
            tool_name: Name of the tool being called
            arguments: Dictionary of arguments passed to the tool
            result: Result returned by the tool (optional)
            error: Error message if the call failed (optional)
        """
        timestamp = datetime.now().isoformat()
        
        # Create structured log entry
        log_entry = {
            "timestamp": timestamp,
            "tool": tool_name,
            "arguments": arguments,
            "result": str(result)[:200] if result else None,  # Truncate long results
            "error": error,
            "success": error is None
        }
        
        # Write to tool-specific JSONL file
        log_file = self._get_log_file(tool_name)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Also log human-readable version to console
        self._log_human_readable(tool_name, arguments, result, error)
    
    def _log_human_readable(self, tool_name: str, arguments: Dict[str, Any], result: Any, error: str):
        """Log in human-readable format to console."""
        
        # Format arguments nicely
        args_str = self._format_arguments(arguments)
        
        if error:
            logger.error(f"\n{'='*60}\n❌ TOOL CALL FAILED: {tool_name}\n{args_str}\nError: {error}\n{'='*60}")
        else:
            result_preview = str(result)[:100] if result else "None"
            logger.info(f"\n{'='*60}\n✅ TOOL CALL: {tool_name}\n{args_str}\nResult: {result_preview}...\n{'='*60}")
    
    def _format_arguments(self, arguments: Dict[str, Any]) -> str:
        """Format arguments for readable display."""
        lines = ["Arguments:"]
        for key, value in arguments.items():
            # Truncate long values
            if isinstance(value, str) and len(value) > 100:
                value_display = f"{value[:97]}... ({len(value)} chars)"
            else:
                value_display = value
            lines.append(f"  - {key}: {value_display}")
        return '\n'.join(lines)


# Global logger instance
_tool_call_logger = None

def get_tool_call_logger(log_dir: Path = None) -> ToolCallLogger:
    """Get or create the global tool call logger."""
    global _tool_call_logger
    if _tool_call_logger is None:
        _tool_call_logger = ToolCallLogger(log_dir)
    return _tool_call_logger


def log_tool_call(tool_name: str, arguments: Dict[str, Any], result: Any = None, error: str = None):
    """Convenience function to log a tool call."""
    logger = get_tool_call_logger()
    logger.log_call(tool_name, arguments, result, error)
