from app.services.captcha_detection.strategies.base import DetectionStrategy
from app.services.captcha_detection.models import CaptchaResult
from app.services.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel


class URLPatternDetectionStrategy(DetectionStrategy):
    def detect(self) -> CaptchaResult:
        return self._safe_execute(self._check_url_patterns, "URL Pattern CAPTCHA")
    
    def _check_url_patterns(self) -> CaptchaResult:
        url = self.driver.current_url.lower()

        for pattern in CaptchaPatterns.URL_PATTERNS:
            if pattern in url:
                return CaptchaResult(
                    detected=True,
                    captcha_type="URL Pattern CAPTCHA",
                    details=f"Found CAPTCHA pattern '{pattern}' in URL: {url}",
                    confidence=ConfidenceLevel.MEDIUM
                )
        return CaptchaResult(detected=False)