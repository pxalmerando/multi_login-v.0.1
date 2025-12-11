from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from app.captcha_detection.strategies.base import DetectionStrategy
from app.captcha_detection.models import CaptchaResult
from app.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel


class HCaptchaDetectionStrategy(DetectionStrategy):

    def detect(self) -> CaptchaResult:

        return self._safe_execute(self._check_hcaptcha, "hCaptcha")
    
    def _check_hcaptcha(self) -> CaptchaResult:
        result = self._check_iframes()
        if result.detected:
            return result
        return self._check_dom_elements()   

    def _check_iframes(self) -> CaptchaResult:
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

        for iframe in iframes:
            src = iframe.get_attribute("src") or ""

            if any(domain in src for domain in CaptchaPatterns.HCAPTCHA_DOMAINS):
                return CaptchaResult(
                    detected=True,
                    captcha_type="hCaptcha",
                    details=f"Found hCaptcha iframe with src: {src}",
                    confidence=ConfidenceLevel.HIGH
                )
        return CaptchaResult(detected=False)
    
    def _check_dom_elements(self) -> CaptchaResult:

        for by, value in CaptchaPatterns.HCAPTCHA_SELECTORS:
            try:
                self.driver.find_element(by, value)
                return CaptchaResult(
                    detected=True,
                    captcha_type="hCaptcha",
                    details=f"Found hCaptcha DOM element with {by}={value}",
                    confidence=ConfidenceLevel.HIGH
                )
            except NoSuchElementException:
                continue
        return CaptchaResult(detected=False)