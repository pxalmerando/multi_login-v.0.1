"""WebSocket routes for URL processing with authentication."""
import logging
from typing import Optional
from fastapi import status
from jose import jwt, JWTError
from app.core.config import SECRET_KEY, ALGORITHM
from app.database.profile_repository import ProfileRepository
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.multi_login_service import MultiLoginService
from app.services.redis_profile_storage import RedisProfileStorage
from app.api.websocket.websocket_handlers import process_multiple_urls
from app.services.profile_allocation_service import ProfileAllocationService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)


@router.websocket("/process_urls")
async def process_urls(
    websocket: WebSocket,
    token: str
):
    """Process multiple URLs via WebSocket with JWT authentication."""
    
    
    if token is None:
        await websocket.close(code=4001, reason="No token provided")
        return
    
    try:
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=[str(ALGORITHM)])
        email: Optional[str] = payload.get("sub")
        if email is None:
            await websocket.close(code=4002, reason="Invalid token payload")
            return
    except JWTError as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
        return
    
    
    await websocket.accept()
    await websocket.send_json({
        "status": "connected",
        "message": f"Authenticated as {email}"
    })
    
    
    redis_storage = RedisProfileStorage()
    multi_login_service = MultiLoginService()
    
    try:
        await redis_storage.initialize()
        await multi_login_service.initialize()
        
        profile_repo = ProfileRepository(multi_login_service=multi_login_service)
        profile_storage = redis_storage
        profile_allocator = ProfileAllocationService(
            repository=profile_repo, 
            storage=profile_storage
        )

        while True:
            data = await websocket.receive_json()
            urls = data.get("urls", [])
            
            if not urls or not isinstance(urls, list):
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid URLs provided - expected a list of URLs"
                })
                continue
                
            valid_urls = [url for url in urls if url and isinstance(url, str)]
            
            if not valid_urls:
                await websocket.send_json({
                    "status": "error", 
                    "message": "No valid URLs provided"
                })
                continue
            
            await process_multiple_urls(
                websocket=websocket,
                urls=valid_urls,
                multi_login_service=multi_login_service,
                profile_allocator=profile_allocator,
            )
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {email}")
        await redis_storage.close()
        await redis_storage.flush()
    except Exception as e:
        logger.exception(f"Error for {email}: {e}")
        try:
            await websocket.send_json({
                "status": "error",
                "message": f"Unexpected server error: {str(e)}"
            })
        except Exception:
            pass  
    finally:
        
        await redis_storage.flush()
        await redis_storage.close()
        await multi_login_service.cleanup()
        logger.info(f"Cleanup complete for {email}")