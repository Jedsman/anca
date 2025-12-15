import json
import logging
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgentSettings(BaseModel):
    provider: str
    model: str

class AgentsConfig(BaseModel):
    agents: Dict[str, AgentSettings]

# Default Configuration
DEFAULT_CONFIG = {
    "default": {"provider": "gemini", "model": "gemini-1.5-flash-latest"},
    "planner": {"provider": "gemini", "model": "gemini-1.5-pro-latest"},
    "researcher": {"provider": "gemini", "model": "gemini-1.5-flash-latest"},
    "writer": {"provider": "gemini", "model": "gemini-1.5-flash-latest"},
    "trend_analyzer": {"provider": "gemini", "model": "gemini-1.5-flash-latest"},
    "editor": {"provider": "gemini", "model": "gemini-1.5-pro-latest"},
    "auditor": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
    "refiner": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
    "fact_checker": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
    "assembler": {"provider": "gemini", "model": "gemini-1.5-flash-latest"}
}

class AgentConfigManager:
    _instance = None
    _config: Optional[AgentsConfig] = None
    _config_path: Path = settings.root_dir / "agent_config.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load config from disk or create default"""
        if not self._config_path.exists():
            logger.info("Agent config not found, creating default.")
            self._save_config_dict(DEFAULT_CONFIG)
            self._config = AgentsConfig(agents={k: AgentSettings(**v) for k, v in DEFAULT_CONFIG.items()})
        else:
            try:
                with open(self._config_path, 'r') as f:
                    data = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_CONFIG.copy()
                merged.update(data if "agents" not in data else data["agents"]) # Handle both wrapped and unwrapped
                
                # If structure is valid
                self._config = AgentsConfig(agents={k: AgentSettings(**v) for k, v in merged.items()})
            except Exception as e:
                logger.error(f"Failed to load agent config: {e}. Reverting to defaults.")
                self._config = AgentsConfig(agents={k: AgentSettings(**v) for k, v in DEFAULT_CONFIG.items()})

    def _save_config_dict(self, data: dict):
        with open(self._config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_config(self) -> AgentsConfig:
        if self._config is None:
            self._load_config()
        return self._config

    def update_config(self, new_config: AgentsConfig):
        """Update and save config"""
        data = {k: v.model_dump() for k, v in new_config.agents.items()}
        self._save_config_dict(data)
        self._config = new_config
        logger.info("Agent configuration updated.")

    def get_agent_settings(self, agent_name: str) -> AgentSettings:
        """Get settings for a specific agent, falling back to default"""
        config = self.get_config()
        return config.agents.get(agent_name, config.agents.get("default"))

agent_config = AgentConfigManager()
