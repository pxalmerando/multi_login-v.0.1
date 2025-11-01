from fastapi import WebSocket
from typing import Optional
from enum import Enum


class NotificationStatus(Enum):
    CONNECTED = "connected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"


class WebSocketNotifier:
    def __init__(
        self, 
        websocket: WebSocket
    ):
        self.websocket = websocket
    
    async def send_status(
            self, 
            status: NotificationStatus, 
            message: str,
            data: Optional[dict] = None,
            step: Optional[int] = None, 
            total_steps: Optional[int] = None
    ):
        
        payload = {
            "status": status.value,
            "message": message,
        }

        if data:
            payload["data"] = data
        
        if step is not None and total_steps is not None:
            payload["step"] = step
            payload["total_steps"] = total_steps

        await self.websocket.send_json(payload)
    async def notify_processing(
        self, 
        message: str,
        step: int,
        total_steps: int
    ):
        await self.send_status(
            NotificationStatus.PROCESSING,
            message=message,
            step=step,
            total_steps=total_steps
        )
    async def notify_completed(
        self, 
        message: str,
        data: dict
    ):
        await self.send_status(
            status=NotificationStatus.COMPLETED,
            message=message,
            data=data
        )
    
    async def notify_error(
            self,
            message: str
    ):
        await self.send_status(
            status=NotificationStatus.ERROR,
            message=message
        )
    
    async def notify_batch_started(
            self,
            total_urls: list[str],
            max_concurrent: int
    ):
        
        await self.send_status(
            status=NotificationStatus.BATCH_STARTED,
            message=f"Processing {len(total_urls)} URLs (max {max_concurrent} concurrent)",
            data={
                "total_urls": len(total_urls),
            }
        )

    async def notify_batch_completed(
            self,
            total_urls: int,
            successful_urls: int,
            failed_urls: int
    ):
        await self.send_status(
            status=NotificationStatus.BATCH_COMPLETED,
            message=f"Processing completed. {successful_urls} URLs processed successfully. {failed_urls} URLs failed to process.",
            data={
                "total_urls": total_urls,
                "successful_urls": successful_urls,
                "failed_urls": failed_urls
            }
        )






