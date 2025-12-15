"""
Publishing Routes
Trigger WordPress publishing tool via API
"""
from fastapi import APIRouter, HTTPException, status
import logging
import subprocess
import sys
from pathlib import Path

import requests
import base64

from app.schemas.models import PublishRequest, DeletePublishedRequest, ErrorResponse
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Publishing"])

@router.post(
    "/publish",
    summary="Publish an article to WordPress",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Article published successfully"},
        404: {"model": ErrorResponse, "description": "Article not found"},
        500: {"model": ErrorResponse, "description": "Publishing failed"}
    }
)
async def publish_article(request: PublishRequest):
    """
    Trigger the WordPress Publisher tool for a specific article.
    """
    # 1. Validate File Exists
    # The request.filename might be just the name or relative path. 
    # We assume it's in the articles directory.
    filename = Path(request.filename).name # Security: force basename
    article_path = settings.articles_dir / filename
    
    if not article_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{filename}' not found in {settings.articles_dir}"
        )

    # 2. Construct Command
    # uv run python tools/wordpress_publisher.py [file] --url [url] --user [user] --password [pass] --status [status]
    # We use sys.executable to ensure we use the same python env, or "uv run" if preferred.
    # Since we are inside the running app (likely docker or uv), using the same python interpreter
    # to run the tool script is usually safer, provided deps are installed.
    # However, the user runs with `uv run`. Let's try direct python execution of the tool script.
    
    tool_path = Path("tools/wordpress_publisher.py").resolve()
    if not tool_path.exists():
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Publisher tool not found on server"
        )

    cmd = [
        sys.executable,
        str(tool_path),
        str(article_path),
        "--url", request.wp_url,
        "--user", request.wp_user,
        "--password", request.wp_password,
        "--status", request.status
    ]

    logger.info(f"Executing publisher: {' '.join(cmd)}")

    try:
        # Run subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log output
        logger.info(f"Publisher Output: {result.stdout}")
        
        # Parse output for Link/ID from stderr (logging)
        link = None
        post_id = None
        import re
        
        link_match = re.search(r"Link: (https?://\S+)", result.stderr)
        if link_match:
            link = link_match.group(1)
            
        id_match = re.search(r"ID: (\d+)", result.stderr)
        if id_match:
            post_id = int(id_match.group(1))
            
        return {
            "message": "Published successfully",
            "link": link,
            "id": post_id,
            "details": result.stderr 
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Publisher failed: {e.stderr}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Publishing failed: {e.stderr}"
        )
    except Exception as e:
        logger.error(f"Error invoking publisher: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post(
    "/publish/delete",
    summary="Delete a published article from WordPress",
    responses={
        200: {"description": "Article deleted successfully"},
        500: {"model": ErrorResponse, "description": "Deletion failed"}
    }
)
async def delete_published_article(request: DeletePublishedRequest):
    """
    Delete a post from WordPress by ID.
    Force delete to bypass trash.
    """
    api_url = f"{request.wp_url.rstrip('/')}/wp-json/wp/v2/posts/{request.id}"
    
    credentials = f"{request.wp_user}:{request.wp_password}"
    token = base64.b64encode(credentials.encode()).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {token}'
    }
    
    try:
        # force=true bypasses trash
        response = requests.delete(f"{api_url}?force=true", headers=headers, verify=False)
        response.raise_for_status()
        
        logger.info(f"Deleted WP Post ID: {request.id}")
        return {"message": "Deleted successfully", "id": request.id}
        
    except Exception as e:
        logger.error(f"Failed to delete WP post {request.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
