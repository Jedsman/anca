from fastapi import APIRouter, HTTPException
from app.core.agent_config import agent_config, AgentsConfig

router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])

@router.get("/agents", response_model=AgentsConfig)
async def get_agent_config():
    """Get current agent configuration"""
    return agent_config.get_config()

@router.post("/agents", response_model=AgentsConfig)
async def update_agent_config(config: AgentsConfig):
    """Update agent configuration"""
    try:
        agent_config.update_config(config)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
