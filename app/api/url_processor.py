"""URL processing API endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.models.models import URLProcessRequest, URLProcessResponse, User
from app.dependencies import get_current_active_user


router = APIRouter()


@router.post("/process_url", response_model=URLProcessResponse)
def process_url(
    url: URLProcessRequest,
    user: User = Depends(get_current_active_user)
):
    """Process a URL for the authenticated user."""
    return URLProcessResponse(
        success=True,
        submitted_url=url.url,
        result={"status": "success"},
        processed_at=datetime.now(timezone.utc).isoformat(),
        processed_by=user.email,
    )