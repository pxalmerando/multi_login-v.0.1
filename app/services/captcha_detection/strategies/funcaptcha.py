from selenium.webdriver.common.by import By

from app.services.captcha_detection.strategies.base import DetectionStrategy
from app.services.captcha_detection.models import CaptchaResult
from app.services.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel


class FunCaptchaDetectionStrategy(DetectionStrategy):

    def detect(self) -> CaptchaResult:
        return self._safe_execute(self._check_funcaptcha, "FunCaptcha")
    
    def _check_funcaptcha(self) -> CaptchaResult:
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

        for iframe in iframes:
            src = iframe.get_attribute("src") or ""

            if any(domain in src for domain in CaptchaPatterns.FUNCAPTCHA_DOMAINS):
                return CaptchaResult(
                    detected=True,
                    captcha_type="FunCaptcha",
                    details=f"Found FunCaptcha iframe with src: {src}",
                    confidence=ConfidenceLevel.HIGH
                )
        return CaptchaResult(detected=False)
    