from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from app.services.captcha_detection.strategies.base import DetectionStrategy
from app.services.captcha_detection.models import CaptchaResult
from app.services.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel



class RecaptchaDetectionStrategy(DetectionStrategy):
    def detect(self) -> CaptchaResult:
        return self._safe_execute(self._check_recaptcha, "reCAPTCHA")

    def _check_recaptcha(self) -> CaptchaResult:
        results = self._check_iframes()
        if results.detected:
            return results
        return self._check_dom_elements()

    def _check_iframes(self) -> CaptchaResult:
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            title = iframe.get_attribute("title") or ""

            if any(domain in src for domain in CaptchaPatterns.RECAPTCHA_DOMAINS or \
                    "recaptcha" in title.lower()):
                
                return CaptchaResult(
                    detected=True,
                    captcha_type="reCAPTCHA",
                    details=f"Found reCAPTCHA iframe with src: {src}",
                    confidence=ConfidenceLevel.HIGH
                )
        return CaptchaResult(detected=False)
    
    def _check_dom_elements(self) -> CaptchaResult:
        for by, value in CaptchaPatterns.RECAPTCHA_SELECTORS:
            try:
                self.driver.find_element(by, value)
                return CaptchaResult(
                    detected=True,
                    captcha_type="reCAPTCHA",
                    details=f"Found reCAPTCHA DOM element with {by}={value}",
                    confidence=ConfidenceLevel.MEDIUM
                )
            except NoSuchElementException:
                continue
        return CaptchaResult(detected=False)