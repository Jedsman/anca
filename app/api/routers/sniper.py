from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
import logging
import asyncio

from app.core.logging_sniper import get_sniper_logger
from app.core.config_sniper import sniper_settings
from app.state_sniper import ArbitrageState
from run_sniper import app as sniper_graph

router = APIRouter(
    prefix="/api/v1/sniper",
    tags=["Sniper"]
)

logger = get_sniper_logger("API.Sniper")

# -- In-Memory Job Store (MVP) --
# In a real app, use a DB.
current_job = {
    "status": "idle", # idle, running, completed, failed
    "result": None,
    "error": None,
    "logs": [] 
}

class RunRequest(BaseModel):
    query: Optional[str] = None
    min_profit: float = 10.0
    auto: bool = False
    discover: bool = False
    mock: bool = False

class RunResponse(BaseModel):
    status: str
    message: str

def run_sniper_task(req: RunRequest):
    global current_job
    current_job["status"] = "running"
    current_job["result"] = None
    current_job["error"] = None
    
    logger.info(f"Starting Sniper Task via API. Mode: Discover={req.discover}, Auto={req.auto}, Query={req.query}")
    
    # Update Settings
    sniper_settings.min_profit_margin = req.min_profit
    sniper_settings.mock_ebay = req.mock
    
    # Initial State
    initial_state = {
        "search_query": req.query,
        "niche": None,
        "pending_queries": [],
        "raw_listings": [],
        "targets_for_valuation": [],
        "final_deals": [],
        "error_message": None,
        "is_complete": False,
        "is_autonomous": req.auto or req.discover
    }
    
    # Logic for implicit discover mode if no query
    if not req.query and not req.discover:
        # If calling via API without query, assume discover?
        # The CLI logic did this.
        # But here we obey explicit flags more.
        pass

    try:
        # Run Graph
        final_state = sniper_graph.invoke(initial_state)
        
        current_job["status"] = "completed"
        current_job["result"] = {
            "niche": final_state.get("niche"),
            "deals": final_state.get("final_deals", []),
            "pending_queries": final_state.get("pending_queries", [])
        }
        logger.info("Sniper Task Completed successfully.")
        
    except Exception as e:
        logger.exception("Sniper Task Failed")
        current_job["status"] = "failed"
        current_job["error"] = str(e)

@router.post("/run", response_model=RunResponse)
async def trigger_run(req: RunRequest, background_tasks: BackgroundTasks):
    if current_job["status"] == "running":
        raise HTTPException(status_code=400, detail="Job already running")
    
    background_tasks.add_task(run_sniper_task, req)
    return {"status": "started", "message": "Sniper agent started in background"}

@router.get("/status")
async def get_status():
    return current_job

@router.get("/results")
async def get_results():
    if current_job["status"] == "running":
         return {"status": "running", "result": None}
    return current_job

@router.get("/rate-limit")
async def get_rate_limit():
    """Get current eBay API rate limit status."""
    from tools.ebay_tool import EbayTool
    return EbayTool.get_rate_limit_status()
