import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import slugify

logger = logging.getLogger(__name__)

class TopicManager:
    def __init__(self, storage_file: str = "data/topics.json"):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.topics = self._load_topics()

    def _load_topics(self) -> List[Dict]:
        """Load topics from JSON file."""
        if not self.storage_file.exists():
            return []
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading topics: {e}")
            return []

    def _save(self):
        """Save topics to JSON file."""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.topics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving topics: {e}")

    def is_duplicate(self, topic: str) -> bool:
        """Check if topic exists (fuzzy or exact)."""
        # Simple exact slug match for now
        # Could be enhanced with fuzzy matching or semantic similarity later
        slug = slugify.slugify(topic)
        for t in self.topics:
            if t.get("slug") == slug:
                return True
        return False

    def save_topic(self, topic: str, niche: Optional[str] = None):
        """Save a new completed topic."""
        if self.is_duplicate(topic):
            logger.warning(f"Topic already exists: {topic}")
            return

        entry = {
            "topic": topic,
            "slug": slugify.slugify(topic),
            "created_at": datetime.now().isoformat(),
            "status": "completed",
            "niche": niche
        }
        self.topics.append(entry)
        self._save()
        logger.info(f"Topic saved: {topic}")

    def get_recent_topics(self, limit: int = 10) -> List[str]:
        """Get recently generated topics."""
        # topics are appended, so last is newest
        return [t["topic"] for t in self.topics[-limit:]]
