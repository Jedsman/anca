"""
ANCA Job Service
Handles background job execution and tracking
"""
from typing import Dict, Optional
from datetime import datetime
import uuid
import logging
import sys
from pathlib import Path
import re

# Add root directory to sys.path to allow importing run_crew
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.schemas.models import JobResponse, JobStatusEnum
from app.core.config import settings
from run_crew import crew

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing content generation jobs"""

    def __init__(self):
        self.jobs: Dict[str, dict] = {}

    def _extract_filename_from_result(self, result_str: str) -> Optional[str]:
        """Extract the filename from the crew result output.

        Tries multiple extraction methods in order:
        1. JSON parsing (if agent outputs structured JSON)
        2. Regex patterns (for natural language outputs)
        """
        import json

        # Method 1: Try JSON parsing first (most reliable)
        try:
            # Look for JSON-like structure in the result
            result_clean = result_str.strip()
            if result_clean.startswith('{') and result_clean.endswith('}'):
                result_json = json.loads(result_clean)
                if 'filename' in result_json:
                    return result_json['filename']
        except (json.JSONDecodeError, ValueError):
            pass

        # Method 2: Regex patterns (fallback for natural language)
        patterns = [
            r'Article written to:\s*([^\s\n]+\.md)',
            r'Revision complete:\s*([^\s\n]+\.md)',
            r'saved to:\s*([^\s\n]+\.md)',
            r'wrote to:\s*([^\s\n]+\.md)',
            r'filename["\']?:\s*["\']?([^\s\n"\']+\.md)',
            r'"filename":\s*"([^"]+\.md)"',  # JSON field in text
        ]
        for pattern in patterns:
            match = re.search(pattern, result_str, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _construct_filename_from_topic(self, topic: str) -> str:
        """Construct expected filename from topic"""
        # Convert topic to slug: lowercase, replace spaces/special chars with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')
        return f"{slug}.md"

    def _validate_job_completion(self, job_id: str, result_str: str, topic: str = None) -> tuple[bool, Optional[str]]:
        """
        Validate that a job actually completed successfully.
        Returns (is_valid, error_message)
        """
        # Check 1: Result should not be empty or None
        if not result_str or len(result_str.strip()) < 50:
            return False, "Result output is too short or empty"

        # Check 2: Look for article filename in result
        filename = self._extract_filename_from_result(result_str)
        
        # Fallback: construct filename from topic if not found in result
        if not filename and topic:
            filename = self._construct_filename_from_topic(topic)
            logger.warning(f"Job {job_id}: Could not extract filename, trying constructed name: {filename}")

        # Check 3: Verify the file exists
        if filename:
            article_path = settings.articles_dir / filename
            if not article_path.exists():
                # Try without leading path components
                clean_filename = article_path.name
                article_path = settings.articles_dir / clean_filename
                if not article_path.exists():
                    return False, f"Article file not found: {filename}. Agent may have failed to call FileWriterTool."

            # Check 4: Verify file has SUBSTANTIAL content (not empty or stub)
            try:
                with open(article_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Empty file detection
                    if len(content.strip()) == 0:
                        return False, f"Article file is EMPTY: {filename}. Agent did not save content correctly."
                    
                    # Minimum word count check (at least 500 words for basic article)
                    word_count = len(content.split())
                    if word_count < 200:
                        return False, f"Article too short: {word_count} words (minimum 200). File may be corrupted or incomplete."
                    
                    logger.info(f"Job {job_id}: Validated article {filename} ({len(content)} chars, ~{word_count} words)")
            except Exception as e:
                return False, f"Error reading article file: {e}"
        else:
            # No filename found and couldn't construct one
            return False, "Could not determine output filename from agent response"

        # Check 5: Look for signs of actual work (scraping, sources, etc.)
        result_lower = result_str.lower()
        has_sources = 'source' in result_lower or 'url' in result_lower or 'http' in result_lower

        if not has_sources:
            logger.warning(f"Job {job_id}: Result does not mention sources or URLs")

        return True, None
    
    def create_job(self, topic: str) -> JobResponse:
        """Create a new content generation job"""
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "status": JobStatusEnum.PENDING,
            "topic": topic,
            "created_at": datetime.now(),
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        self.jobs[job_id] = job_data
        logger.info(f"Created job {job_id} for topic: {topic}")
        
        return JobResponse(**job_data)
    
    def get_job(self, job_id: str) -> JobResponse:
        """Get job status by ID"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        return JobResponse(**self.jobs[job_id])
    
    def list_jobs(self) -> list:
        """List all jobs"""
        return [JobResponse(**job) for job in self.jobs.values()]
    
    def run_job(self, job_id: str):
        """Execute a content generation job with validation"""
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return

        try:
            logger.info(f"Starting job {job_id} for topic: {self.jobs[job_id]['topic']}")
            self.jobs[job_id]["status"] = JobStatusEnum.RUNNING

            topic = self.jobs[job_id]["topic"]

            # Execute the crew
            result = crew.kickoff(inputs={'topic': topic})
            result_str = str(result)

            # Validate the result (pass topic for fallback filename construction)
            is_valid, error_msg = self._validate_job_completion(job_id, result_str, topic)

            if is_valid:
                self.jobs[job_id]["status"] = JobStatusEnum.COMPLETED
                self.jobs[job_id]["completed_at"] = datetime.now()
                self.jobs[job_id]["result"] = result_str
                logger.info(f"Job {job_id} completed successfully with validation")
            else:
                # Mark as failed if validation fails
                self.jobs[job_id]["status"] = JobStatusEnum.FAILED
                self.jobs[job_id]["completed_at"] = datetime.now()
                self.jobs[job_id]["error"] = f"Validation failed: {error_msg}"
                self.jobs[job_id]["result"] = result_str  # Store partial result for debugging
                logger.error(f"Job {job_id} validation failed: {error_msg}")

        except Exception as e:
            logger.error(f"Job {job_id} failed with exception: {e}", exc_info=True)
            self.jobs[job_id]["status"] = JobStatusEnum.FAILED
            self.jobs[job_id]["completed_at"] = datetime.now()
            self.jobs[job_id]["error"] = str(e)


# Singleton instance
job_service = JobService()
