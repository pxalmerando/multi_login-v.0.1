from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from app.captcha_detection.strategies.base import DetectionStrategy
from app.captcha_detection.models import CaptchaResult
from app.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel


class GenericDetectionStrategy(DetectionStrategy):

    def detect(self) -> CaptchaResult:
        return self._safe_execute(self._check_generic, "Generic CAPTCHA")

    def _check_generic(self) -> CaptchaResult:
        for selector in CaptchaPatterns.GENERIC_SELECTORS:
            result = self._check_selector(By.CLASS_NAME, selector)
            
            if result.detected:
                return result
            
            result = self._check_selector(By.ID, selector)
            if result.detected:
                return result

        return CaptchaResult(detected=False)

    def _check_selector(self, by: By, value: str) -> CaptchaResult:
        try:
            element = self.driver.find_element(by, value)
            if element.is_displayed():
                return CaptchaResult(
                    detected=True,
                    captcha_type="Generic CAPTCHA",
                    details=f"Found generic CAPTCHA element with {by}={value}",
                    confidence=ConfidenceLevel.MEDIUM
                )
        except NoSuchElementException:
            pass
        
        return CaptchaResult(detected=False)