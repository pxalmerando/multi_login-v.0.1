from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.multi_login_service import MultiLoginService
from app.api.websocket.websocket_handlers import process_url
from app.core.config import SECRET_KEY, ALGORITHM
from fastapi import status
from jose import jwt, JWTError

router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)


@router.websocket("/process_url")
async def connect(
    websocket: WebSocket,
    token: str
):
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

    await websocket.accept()
    await websocket.send_json({
        "status": "connected",
        "message": f"Authenticated as {user['email']}"
    })

    processor = MultiLoginService()
    active_profile_id = None


    try:
        while True:
            data = await websocket.receive_json()
            url = data.get("url")
            if not url:
                await websocket.send_json({
                    "status": "error",
                    "message": "No URL provided"
                })
                continue
            
            active_profile_id = processor.profile_id
            await process_url(url=url, processor=processor, websocket=websocket)

    except WebSocketDisconnect:
        print(f"Disconnected: {user['email']}")
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": f"Unexpected server error: {str(e)}"
        })
    finally:
        # Cleanup the specific profile or all profiles
        if active_profile_id:
            processor.stop_profile(active_profile_id)
        else:
            processor.cleanup()
