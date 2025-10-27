"""URL processing API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from app.models.models import URLProcessRequest, User
from app.dependencies import get_current_active_user
from app.multi_login.service import MultiLoginService


router = APIRouter(
    prefix="/url",
    tags=["url-processing"],
)
multi_login = MultiLoginService()

@router.post("/process_url")
def process_url(
    url: URLProcessRequest,
    user: User = Depends(get_current_active_user),
):
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    results = multi_login.process_url(url=url.url)

    return results