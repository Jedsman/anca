"""
Discovery Router
Endpoints for interactive topic discovery
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
from typing import List

from app.schemas.models import DiscoverRequest, DiscoverResponse
from agents.trend_analyzer import trend_analyzer_node

router = APIRouter(prefix="/api/v1", tags=["Discovery"])
logger = logging.getLogger(__name__)

@router.post("/discover_topics", response_model=DiscoverResponse)
async def discover_topics(request: DiscoverRequest):
    """
    Run the Trend Analyzer to discover potential topics.
    Does NOT start a job. Returns a list of topics for user selection.
    """
    try:
        logger.info(f"Starting discovery for niche: {request.niche} (Affiliate: {request.affiliate})")

        # Construct minimal state for the node
        state = {
            "niche": request.niche,
            "affiliate": request.affiliate,
            "provider": request.provider,
            "model": request.model,
            "interactive": True, # Force interactive mode to get list
            "topic": "Discovery Placeholder" # Required by state schema but ignored by node logic in this context
        }

        # Run the node directly
        # Note: trend_analyzer_node is synchronous, but fast enough (~5-10s)
        # If it becomes too slow, we should wrap it in run_in_executor
        result = trend_analyzer_node(state)
        
        candidates = result.get("topic_candidates", [])
        
        # Fallback if no list returned (shouldn't happen with interactive=True)
        if not candidates and result.get("topic"):
            candidates = [result["topic"]]

        return DiscoverResponse(
            topics=candidates,
            count=len(candidates)
        )

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
