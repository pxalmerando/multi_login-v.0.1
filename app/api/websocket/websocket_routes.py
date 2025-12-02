"""WebSocket routes for URL processing with authentication."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websocket.websocket_handlers import process_multiple_urls
from app.core.config import SECRET_KEY, ALGORITHM
from fastapi import status
from jose import jwt, JWTError
from app.services.multi_login_service import MultiLoginService
from app.services.profile_allocation_service import ProfileAllocationService
from app.database.profile_repository import ProfileRepository
from app.services.profile_state_manager import ProfileStateManager
from app.services.redis_profile_storage import RedisProfileStorage
router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)
@router.websocket("/process_urls")
async def process_urls(
    websocket: WebSocket,
    token: str
):
    """Process multiple URLs via WebSocket with JWT authentication.

    Authenticates the user using the provided JWT token, then listens for URL lists
    to process using the multi-login service and profile allocation.

    Args:
        websocket (WebSocket): The WebSocket connection for communication.
        token (str): JWT token for user authentication.
    """
    if token is None:
        raise Exception("No token provided")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise Exception("Invalid token payload")
        user = {"email": email}
    except JWTError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e),
        )
        print(f"Failed to decode token: {e}")
        return
    await websocket.accept()
    await websocket.send_json({
        "status": "connected",
        "message": f"Authenticated as {user['email']}"
    })
    
    redis = RedisProfileStorage()
    await redis.initialize()
    multi_login_service = MultiLoginService()
    await multi_login_service.initialize()
    profile_repo = ProfileRepository(multi_login_service=multi_login_service)
    profile_state = ProfileStateManager(redis)
    profile_allocator = ProfileAllocationService(repository=profile_repo, state_manager=profile_state)

    try:
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
        print(f"WebSocket disconnected: {user['email']}")
        await multi_login_service.cleanup()
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": f"Unexpected server error: {str(e)}"
        })
        await multi_login_service.cleanup()

@router.websocket("/process_url")
async def process_single_url(
    websocket: WebSocket,
    token: str
):
    """Process a single URL via WebSocket with JWT authentication.

    Authenticates the user using the provided JWT token, then listens for single URLs
    to process using the multi-login service and profile allocation with concurrency set to 1.

    Args:
        websocket (WebSocket): The WebSocket connection for communication.
        token (str): JWT token for user authentication.
    """
    if token is None:
        raise Exception("No token provided")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise Exception("Invalid token payload")
        user = {"email": email}

    except JWTError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e),
        )
        print(f"Failed to decode token: {e}")
        return
    
    await websocket.accept()
    await websocket.send_json({
        "status": "connected",
        "message": f"Authenticated as {user['email']} (single url mode)"
    })

    processor = MultiLoginService()
    await processor.initialize()
    profile_allocator = ProfileAllocationService(multi_login_service=processor)

    try:
        while True:
            data = await websocket.receive_json()

            url = data.get("url")
            if not url or not isinstance(url, str):
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid payload — expected {\"url\": \"https://...\"}"
                })
                continue

            await process_multiple_urls(
                websocket=websocket,
                urls=[url],
                processor=processor,
                profile_allocator=profile_allocator,
                max_concurrency=1
            )

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {user['email']}")
        await processor.cleanup()
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": f"Unexpected server error: {str(e)}"
        })
        await processor.cleanup()