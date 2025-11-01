from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websocket.websocket_handlers import process_multiple_urls
from app.core.config import SECRET_KEY, ALGORITHM
from fastapi import status
from jose import jwt, JWTError
from app.services.multi_login_service import MultiLoginService

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
        return

    await websocket.accept()
    await websocket.send_json({
        "status": "connected",
        "message": f"Authenticated as {user['email']}"
    })

    processor = MultiLoginService()
    await processor.initialize()

    try:
        while True:
            data = await websocket.receive_json()
            urls = data.get("urls", [])

            # Better URL validation
            if not urls or not isinstance(urls, list):
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid URLs provided - expected a list of URLs"
                })
                continue

                
            # Filter out any None or empty URLs
            valid_urls = [url for url in urls if url and isinstance(url, str)]
            
            if not valid_urls:
                await websocket.send_json({
                    "status": "error", 
                    "message": "No valid URLs provided"
                })
                continue
            print(valid_urls)

            await process_multiple_urls(
                websocket=websocket,
                urls=valid_urls,
                processor=processor
            )

    except WebSocketDisconnect:
        print(f"Disconnected: {user['email']}")
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": f"Unexpected server error: {str(e)}"
        })
