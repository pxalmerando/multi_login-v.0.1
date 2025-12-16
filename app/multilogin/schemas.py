from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MultiLoginProfileSession:
    status_code: int
    profile_id: str
    selenium_port: int
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


    @property
    def selenium_url(self) -> str:
        return f"http://host.docker.internal:{self.selenium_port}"