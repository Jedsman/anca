"""
LiteLLM callback for logging all LLM requests and responses.
Automatically captures every call to the LLM for debugging.
"""
import logging
from typing import Any, Dict, Optional
from litellm.integrations.custom_logger import CustomLogger
from app.core.llm_call_logger import get_llm_call_logger

logger = logging.getLogger(__name__)


class LLMLoggingCallback(CustomLogger):
    """
    Custom LiteLLM callback that logs all LLM interactions.
    
    This captures:
    - Every prompt sent to the LLM
    - Every response received
    - Token usage
    - Tool calls made
    """
    
    def __init__(self):
        super().__init__()
        self.llm_logger = get_llm_call_logger()
        self._request_cache = {}  # Store request IDs by call_id
    
    def log_pre_api_call(self, model, messages, kwargs):
        """Called before the LLM API call."""
        try:
            call_id = kwargs.get("litellm_call_id", "unknown")
            
            # Extract agent name if available
            agent_name = kwargs.get("metadata", {}).get("agent_name", "Unknown")
            
            # Log the request
            request_id = self.llm_logger.log_request(
                model=model,
                messages=messages,
                agent_name=agent_name,
                tools=kwargs.get("tools"),
                temperature=kwargs.get("temperature")
            )
            
            # Cache the request_id for matching with response
            self._request_cache[call_id] = request_id
            
        except Exception as e:
            logger.error(f"Error logging pre-API call: {e}")
    
    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        """Called when LLM API call succeeds."""
        try:
            call_id = kwargs.get("litellm_call_id", "unknown")
            request_id = self._request_cache.get(call_id, "unknown")
            
            # Extract response details
            if hasattr(response_obj, 'choices') and len(response_obj.choices) > 0:
                choice = response_obj.choices[0]
                message = choice.message if hasattr(choice, 'message') else choice
                
                response_text = getattr(message, 'content', '') or ''
                tool_calls = getattr(message, 'tool_calls', None)
                finish_reason = getattr(choice, 'finish_reason', None)
            else:
                response_text = str(response_obj)
                tool_calls = None
                finish_reason = None
            
            # Extract token usage
            usage = None
            if hasattr(response_obj, 'usage'):
                usage = {
                    "prompt_tokens": getattr(response_obj.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response_obj.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response_obj.usage, 'total_tokens', 0)
                }
            
            # Log the response
            self.llm_logger.log_response(
                request_id=request_id,
                response_text=response_text,
                usage=usage,
                tool_calls=tool_calls,
                finish_reason=finish_reason
            )
            
            # Clean up cache
            if call_id in self._request_cache:
                del self._request_cache[call_id]
                
        except Exception as e:
            logger.error(f"Error logging success event: {e}")
    
    def log_failure_event(self, kwargs, response_obj, start_time, end_time):
        """Called when LLM API call fails."""
        try:
            call_id = kwargs.get("litellm_call_id", "unknown")
            request_id = self._request_cache.get(call_id, "unknown")
            
            error_message = str(response_obj) if response_obj else "Unknown error"
            
            # Log the error
            self.llm_logger.log_response(
                request_id=request_id,
                response_text="",
                error=error_message
            )
            
            # Clean up cache
            if call_id in self._request_cache:
                del self._request_cache[call_id]
                
        except Exception as e:
            logger.error(f"Error logging failure event: {e}")


# Create and register the callback
def setup_llm_logging():
    """Setup LLM logging callback."""
    import litellm
    
    callback = LLMLoggingCallback()
    
    # Add to LiteLLM's callback list
    if callback not in litellm.success_callback:
        litellm.success_callback = [callback]
    if callback not in litellm.failure_callback:
        litellm.failure_callback = [callback]
    if callback not in litellm._async_success_callback:
        litellm._async_success_callback = [callback]
    if callback not in litellm._async_failure_callback:
        litellm._async_failure_callback = [callback]
    
    logger.info("✅ LLM logging callback registered")
