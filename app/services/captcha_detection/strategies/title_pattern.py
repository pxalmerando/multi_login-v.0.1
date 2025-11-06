from app.services.captcha_detection.strategies.base import DetectionStrategy
from app.services.captcha_detection.models import CaptchaResult
from app.services.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel


class TitlePatternDetectionStrategy(DetectionStrategy):
    def detect(self) -> CaptchaResult:
        return self._safe_execute(self._check_title, "Page Title")
    
    def _check_title(self) -> CaptchaResult:
        title = self.driver.title.lower()

        for pattern in CaptchaPatterns.TITLE_PATTERNS:
            if pattern in title:
                return CaptchaResult(
                    detected=True,
                    captcha_type="Title Pattern CAPTCHA",
                    details=f"Found CAPTCHA pattern '{pattern}' in title: {title}",
                    confidence=ConfidenceLevel.MEDIUM
                )
        return CaptchaResult(detected=False)