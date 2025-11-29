from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class ProcessingResult:
    """Result of processing a single URL"""
    success: bool
    url: str
    captcha_detected: bool = False
    web_title: Optional[str] = None
    html_source: Optional[str] = None
    error_message: Optional[str] = None
    processed_at: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for WebSocket transmission"""
        return {
            "success": self.success,
            "url": self.url,
            "web_title": self.web_title,
            "html_source": self.html_source,
            "error_message": self.error_message,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }
    
@dataclass
class BatchProcessingResult:
    total_urls: int
    successful_urls: int
    failed_urls: int
    results: list[ProcessingResult]


    def to_dict(self) -> dict:

        return {
            "total_urls": self.total_urls,
            "successful_urls": self.successful_urls,
            "failed_urls": self.failed_urls,
            "results": [result.to_dict() for result in self.results]
        }
    
@dataclass
class ProfileSession:
    profile_id: str
    selenium_url: str
    selenium_port: int
    started_at: datetime = None

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
    
    
