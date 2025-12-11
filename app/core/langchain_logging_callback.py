"""
LangChain callback handler for logging LLM interactions.
Adapts LangChain events to our existing logger.
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage
from app.core.llm_call_logger import get_llm_call_logger

logger = logging.getLogger(__name__)

class LangChainLoggingHandler(BaseCallbackHandler):
    """Callback handler that logs to our file-based system."""
    
    def __init__(self, agent_name: str = "Unknown"):
        self.llm_logger = get_llm_call_logger()
        self.agent_name = agent_name
        self.current_request_id = None
        
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        try:
            print(f"DEBUG: LangChain Callback Triggered for {serialized.get('name')}")
            # Flatten messages list
            flat_messages = [m for sublist in messages for m in sublist]
            msg_dicts = [{"role": m.type, "content": m.content} for m in flat_messages]
            
            self.current_request_id = self.llm_logger.log_request(
                model=serialized.get("name", "unknown"),
                messages=msg_dicts,
                agent_name=self.agent_name,
                tools=kwargs.get("tools"),
            )
        except Exception as e:
            logger.error(f"Error logging start: {e}")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        try:
            if not self.current_request_id:
                return

            generation = response.generations[0][0]
            output_text = generation.text
            
            # Capture usage if available
            usage = None
            if response.llm_output:
                usage = response.llm_output.get("token_usage") or response.llm_output.get("usage")

            self.llm_logger.log_response(
                request_id=self.current_request_id,
                response_text=output_text,
                usage=usage,
                tool_calls=None # LangChain handles tool parsing differently, mostly in text
            )
        except Exception as e:
            logger.error(f"Error logging end: {e}")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        try:
            if self.current_request_id:
                self.llm_logger.log_response(
                    request_id=self.current_request_id,
                    response_text="",
                    error=str(error)
                )
        except Exception as e:
            logger.error(f"Error logging failure: {e}")
