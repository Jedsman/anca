"""
LLM Request/Response logger for debugging agent behavior.
Captures every prompt sent and response received from LLMs.
"""
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
import hashlib

logger = logging.getLogger(__name__)


class LLMCallLogger:
    """Logs all LLM requests and responses in structured format."""
    
    def __init__(self, log_dir: Path = None):
        from app.core.logging_utils import get_session_log_file
        from app.core.config import settings
        
        self.log_dir = log_dir or Path("logs/llm_calls")
        
        # Use centralized helper for rotation and cleanup
        # We use .jsonl extension for these
        # Use LOG_BACKUP_COUNT from settings
        self.log_file = get_session_log_file(
            "llm_calls", 
            self.log_dir, 
            max_files=settings.log_backup_count,
            extension=".jsonl"
        )
        
        logger.info(f"📝 LLM calls will be logged to: {self.log_file}")
    
    def log_request(
        self,
        model: str,
        messages: list,
        agent_name: str = None,
        tools: list = None,
        temperature: float = None
    ):
        """
        Log an LLM request (prompt being sent).
        
        Args:
            model: Model name (e.g., "ollama/llama3.1:8b")
            messages: List of message dictionaries
            agent_name: Name of the agent making the request
            tools: List of available tools
            temperature: Model temperature
        """
        timestamp = datetime.now().isoformat()
        
        # Generate request ID for matching with response
        request_id = self._generate_request_id(timestamp, messages)
        
        # Extract the actual prompt (usually the last user message)
        prompt_text = self._extract_prompt(messages)
        
        log_entry = {
            "request_id": request_id,
            "timestamp": timestamp,
            "type": "request",
            "agent": agent_name,
            "model": model,
            "temperature": temperature,
            "prompt_preview": prompt_text[:500] if prompt_text else None,
            "prompt_full_length": len(prompt_text) if prompt_text else 0,
            "messages_count": len(messages),
            "tools_available": [t.get("name") if isinstance(t, dict) else str(t) for t in (tools or [])],
            "tools_count": len(tools) if tools else 0
        }
        
        self._write_log(log_entry)
        return request_id
    
    def log_response(
        self,
        request_id: str,
        response_text: str,
        usage: Dict = None,
        tool_calls: list = None,
        finish_reason: str = None,
        error: str = None
    ):
        """
        Log an LLM response.
        
        Args:
            request_id: ID from the corresponding request
            response_text: The LLM's response text
            usage: Token usage dict (prompt_tokens, completion_tokens, total_tokens)
            tool_calls: List of tool calls made by the LLM
            finish_reason: Why generation stopped (e.g., "stop", "tool_calls")
            error: Error message if the request failed
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "request_id": request_id,
            "timestamp": timestamp,
            "type": "response",
            "response_preview": response_text[:500] if response_text else None,
            "response_full_length": len(response_text) if response_text else 0,
            "prompt_tokens": usage.get("prompt_tokens") if usage else None,
            "completion_tokens": usage.get("completion_tokens") if usage else None,
            "total_tokens": usage.get("total_tokens") if usage else None,
            "tool_calls": [tc.get("function", {}).get("name") for tc in (tool_calls or [])],
            "tool_calls_count": len(tool_calls) if tool_calls else 0,
            "finish_reason": finish_reason,
            "error": error,
            "success": error is None
        }
        
        self._write_log(log_entry)
    
    def _extract_prompt(self, messages: list) -> str:
        """Extract the main prompt text from messages."""
        if not messages:
            return ""
        
        # Find the last user or system message
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("content"):
                return msg["content"]
        
        return str(messages[-1]) if messages else ""
    
    def _generate_request_id(self, timestamp: str, messages: list) -> str:
        """Generate a unique ID for this request."""
        content = f"{timestamp}_{str(messages)}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _write_log(self, entry: Dict):
        """Write a log entry to the JSONL file."""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')


# Global logger instance
_llm_call_logger = None

def get_llm_call_logger(log_dir: Path = None) -> LLMCallLogger:
    """Get or create the global LLM call logger."""
    global _llm_call_logger
    if _llm_call_logger is None:
        _llm_call_logger = LLMCallLogger(log_dir)
    return _llm_call_logger


def log_llm_request(model: str, messages: list, **kwargs) -> str:
    """Log an LLM request and return its ID."""
    logger_instance = get_llm_call_logger()
    return logger_instance.log_request(model, messages, **kwargs)


def log_llm_response(request_id: str, response_text: str, **kwargs):
    """Log an LLM response."""
    logger_instance = get_llm_call_logger()
    logger_instance.log_response(request_id, response_text, **kwargs)
