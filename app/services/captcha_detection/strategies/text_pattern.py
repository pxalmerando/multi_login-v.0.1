from selenium.webdriver.common.by import By

from app.services.captcha_detection.models import CaptchaResult
from app.services.captcha_detection.strategies.base import DetectionStrategy
from app.services.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel


class TextPatternDetectionStrategy(DetectionStrategy):
    def detect(self) -> CaptchaResult:
        return self._safe_execute(self._check_text, "Text Pattern")
    
    def _check_text(self) -> CaptchaResult:
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        
            for pattern in CaptchaPatterns.TEXT_PATTERNS:
                if pattern in page_text:
                    return CaptchaResult(
                        detected=True,
                        captcha_type="Text Pattern CAPTCHA",
                        details=f"Found CAPTCHA pattern '{pattern}' in page text.",
                        confidence=ConfidenceLevel.LOW
                    )
            return CaptchaResult(detected=False)
        except Exception as e:
            return CaptchaResult(detected=False)