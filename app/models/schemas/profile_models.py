from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class MultiLoginProfileSession:
    profile_id: str
    selenium_port: int
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


    @property
    def selenium_url(self) -> str:
        return f"http://localhost:{self.selenium_port}"

