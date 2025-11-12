from fastapi import WebSocket
from typing import Optional
from enum import Enum

class NotificationStatus(Enum):
    """Enumeration of possible notification statuses for WebSocket communications."""
    CONNECTED = "connected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"
class WebSocketNotifier:
    """Handles sending status notifications via WebSocket connection."""
    def __init__(
        self,
        websocket: WebSocket
    ):
        """Initialize the WebSocketNotifier with a WebSocket instance.

        Args:
            websocket (WebSocket): The WebSocket connection to send notifications through.
        """
        self.websocket = websocket
    
    async def send_status(
            self,
            status: NotificationStatus,
            message: str,
            data: Optional[dict] = None,
            step: Optional[int] = None,
            total_steps: Optional[int] = None
    ):
        """Send a status notification via WebSocket.

        Args:
            status (NotificationStatus): The status to send.
            message (str): The message to include in the notification.
            data (Optional[dict]): Optional additional data to include.
            step (Optional[int]): Current step number for progress tracking.
            total_steps (Optional[int]): Total number of steps for progress tracking.
        """
        
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
        """Notify that processing is ongoing.

        Args:
            message (str): Description of the current processing step.
            step (int): Current step number.
            total_steps (int): Total number of steps.
        """
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
        """Notify that processing has completed successfully.

        Args:
            message (str): Completion message.
            data (dict): Result data from the processing.
        """
        await self.send_status(
            status=NotificationStatus.COMPLETED,
            message=message,
            data=data
        )
    
    async def notify_error(
            self,
            message: str
    ):
        """Notify that an error occurred during processing.

        Args:
            message (str): Error message.
        """
        await self.send_status(
            status=NotificationStatus.ERROR,
            message=message
        )
    
    async def notify_batch_started(
            self,
            total_urls: int,
            max_concurrent: int
    ):
        """Notify that batch processing has started.

        Args:
            total_urls (int): Total number of URLs to process.
            max_concurrent (int): Maximum number of concurrent processes.
        """
        await self.send_status(
            status=NotificationStatus.BATCH_STARTED,
            message=f"Processing {total_urls} URLs (max {max_concurrent} concurrent)",
            data={"total_urls": total_urls}
        )
    async def notify_batch_completed(
            self,
            total_urls: int,
            successful_urls: int,
            failed_urls: int
    ):
        """Notify that batch processing has completed.

        Args:
            total_urls (int): Total number of URLs processed.
            successful_urls (int): Number of URLs processed successfully.
            failed_urls (int): Number of URLs that failed to process.
        """
        await self.send_status(
            status=NotificationStatus.BATCH_COMPLETED,
            message=f"Processing completed. {successful_urls} URLs processed successfully. {failed_urls} URLs failed to process.",
            data={
                "total_urls": total_urls,
                "successful_urls": successful_urls,
                "failed_urls": failed_urls
            }
        )
