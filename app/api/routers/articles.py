"""
Article Management Routes
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from datetime import datetime
import logging

from app.core.config import settings
from app.schemas.models import ArticleListResponse, ArticleInfo, ErrorResponse, UpdateArticleRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Articles"])


@router.get(
    "/articles",
    response_model=ArticleListResponse,
    summary="List all articles"
)
async def list_articles():
    """List all generated articles with metadata"""
    if not settings.articles_dir.exists():
        return ArticleListResponse(articles=[], total=0)
    
    articles = []
    for file in settings.articles_dir.glob("*.md"):
        stat = file.stat()
        articles.append(ArticleInfo(
            filename=file.name,
            size=stat.st_size,
            created=datetime.fromtimestamp(stat.st_ctime),
            modified=datetime.fromtimestamp(stat.st_mtime)
        ))
    
    return ArticleListResponse(articles=articles, total=len(articles))


@router.get(
    "/articles/{filename}",
    response_class=FileResponse,
    summary="Download an article",
    responses={
        200: {"description": "Article file"},
        404: {"model": ErrorResponse, "description": "Article not found"}
    }
)
async def get_article(filename: str):
    """Retrieve a specific article file"""
    file_path = settings.articles_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{filename}' not found"
        )
    
    return FileResponse(
        file_path,
        media_type="text/markdown",
        filename=filename
    )


@router.delete(
    "/articles/{filename}",
    summary="Delete an article",
    responses={
        200: {"description": "Article deleted"},
        404: {"model": ErrorResponse, "description": "Article not found"}
    }
)
async def delete_article(filename: str):
    """Delete a specific article"""
    file_path = settings.articles_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{filename}' not found"
        )
    
    file_path.unlink()
    logger.info(f"Deleted article: {filename}")
    return {"message": f"Article '{filename}' deleted successfully"}


@router.put(
    "/articles/{filename}",
    summary="Update an article",
    responses={
        200: {"description": "Article updated"},
        404: {"model": ErrorResponse, "description": "Article not found"}
    }
)
async def update_article(filename: str, request: UpdateArticleRequest):
    """Update a specific article file"""
    file_path = settings.articles_dir / filename
    
    # Check if exists (or create? For now only allow edit existing)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{filename}' not found"
        )
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(request.content)
        
    logger.info(f"Updated article: {filename}")
    return {"message": f"Article '{filename}' updated successfully"}
