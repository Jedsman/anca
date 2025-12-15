"""
Logs Router
Exposes endpoints to view application logs
"""
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import logging
import os

from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["System"])
logger = logging.getLogger(__name__)

@router.get("/logs", summary="Get recent application logs")
async def get_logs(lines: int = Query(100, ge=1, le=1000)):
    """
    Retrieve the last N lines from the current session log file.
    """
    try:
        # Find the latest log file
        log_dir = settings.logs_dir
        if not log_dir.exists():
            return {"logs": ["Log directory not found."]}

        # Get all log files matching the pattern
        log_files = list(log_dir.glob("anca_*.log"))
        
        if not log_files:
            return {"logs": ["No log files found."]}

        # Sort by modification time, newest first
        latest_log = max(log_files, key=os.path.getmtime)
        
        # Read the last N lines
        # Efficient checking: Read file, split lines, take tail
        # For huge files, seek() logic is better, but logs rotate at 10MB so read() is okay.
        with open(latest_log, "r", encoding="utf-8", errors="replace") as f:
            content = f.readlines()
            
        recent_logs = content[-lines:]
        return {"logs": [line.rstrip() for line in recent_logs]}

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
