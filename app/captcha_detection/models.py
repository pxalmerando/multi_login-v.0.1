from dataclasses import dataclass
from typing import Optional


@dataclass
class CaptchaResult:
    detected: bool
    captcha_type: Optional[str] = None
    details: str = ""
    confidence: Optional[str] = "none"