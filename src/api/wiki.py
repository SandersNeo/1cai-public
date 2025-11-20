"""
Wiki API Endpoints
Exposes Wiki functionality including Pages, Comments, Search, and Attachments
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.middleware.jwt_user_context import CurrentUser, get_current_user
from src.services.wiki.attachments import WikiAttachmentStorage
from src.services.wiki.comments import CommentDTO, WikiCommentsService
from src.services.wiki.models import WikiPage, WikiPageCreate, WikiPageUpdate
from src.services.wiki.search import WikiSearchService, get_wiki_search_service
from src.services.wiki.service import WikiService
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger
router = APIRouter(prefix="/wiki", tags=["Wiki"])

# --- Dependencies ---


def get_wiki_service():
    """Dependency for WikiService"""
    return WikiService()


def get_comments_service():
    """Dependency for WikiCommentsService"""
    return WikiCommentsService()


def get_attachments_service():
    """Dependency for WikiAttachmentStorage"""
    return WikiAttachmentStorage()


# --- Page Endpoints ---


@router.get("/pages", response_model=List[WikiPage])
async def list_pages(
    limit: int = 50, offset: int = 0, service: WikiService = Depends(get_wiki_service)
):
    """List wiki pages"""
    return await service.list_pages(limit, offset)


@router.get("/pages/{slug}", response_model=WikiPage)
async def get_page(
    slug: str, version: int = None, service: WikiService = Depends(get_wiki_service)
):
    """Get a wiki page by slug"""
    page = await service.get_page(slug, version)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/pages", response_model=WikiPage, status_code=status.HTTP_201_CREATED)
async def create_page(
    data: WikiPageCreate,
    blueprint_id: Optional[str] = None,
    service: WikiService = Depends(get_wiki_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Create a new wiki page"""
    return await service.create_page(
        data, author_id=user.user_id, blueprint_id=blueprint_id
    )


@router.put("/pages/{slug}", response_model=WikiPage)
async def update_page(
    slug: str,
    data: WikiPageUpdate,
    service: WikiService = Depends(get_wiki_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Update a wiki page with optimistic locking"""
    try:
        return await service.update_page(slug, data, author_id=user.user_id)
    except ValueError as e:
        if "Conflict" in str(e):
            raise HTTPException(status_code=409, detail=str(e)) from e
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/preview")
async def preview_content(
    content: str, service: WikiService = Depends(get_wiki_service)
):
    """Render markdown preview"""
    return {"html": await service.render_content(content)}


# --- Search Endpoints ---


@router.get("/search")
async def search_wiki(
    q: str,
    limit: int = 5,
    search_service: WikiSearchService = Depends(get_wiki_search_service),
):
    """Semantic search for wiki pages"""
    return await search_service.search(q, limit)


# --- Comment Endpoints ---


@router.get("/pages/{page_id}/comments", response_model=List[CommentDTO])
async def get_comments(
    page_id: str, comments_service: WikiCommentsService = Depends(get_comments_service)
):
    """Get comments for a page"""
    return await comments_service.get_page_comments(page_id)


@router.post("/pages/{page_id}/comments", response_model=CommentDTO)
async def add_comment(
    page_id: str,
    content: str,
    parent_id: Optional[str] = None,
    comments_service: WikiCommentsService = Depends(get_comments_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Add a comment to a page"""
    return await comments_service.add_comment(page_id, user.user_id, content, parent_id)


# --- Attachment Endpoints ---


@router.post("/attachments/upload")
async def upload_attachment(
    file: UploadFile = File(...),
    storage: WikiAttachmentStorage = Depends(get_attachments_service),
    user: CurrentUser = Depends(get_current_user),
):
    """Upload an attachment to S3"""
    _ = user  # dependency injection check
    content = await file.read()
    url = await storage.upload_file(content, file.filename, file.content_type)

    if not url:
        raise HTTPException(status_code=500, detail="Failed to upload file")

    return {"url": url, "filename": file.filename}


# --- AI Features ---


@router.post("/ask")
async def ask_wiki(query: str, service: WikiService = Depends(get_wiki_service)):
    """Ask AI a question about the Wiki knowledge base"""
    return await service.ask_wiki(query)
