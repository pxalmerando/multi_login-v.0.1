import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from app.services.captcha_detection.models import CaptchaResult
from app.services.captcha_detection.strategies.base import DetectionStrategy
from app.services.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel


class BolBlockDetectionStrategy(DetectionStrategy):

    def detect(self) -> CaptchaResult:
        return self._safe_execute(self._check_bol_block, "BolBlock")
    
    def _check_bol_block(self) -> CaptchaResult:
        url = (self.driver.current_url or "").lower()
        if any(domain in url for domain in CaptchaPatterns.BOL_DOMAINS):
            for by, selector in CaptchaPatterns.BOL_BLOCK_SELECTORS:
                try:
                    element = self.driver.find_element(by, selector)
                    text = element.text.lower()
                    if any(pattern in text for pattern in CaptchaPatterns.BOL_BLOCK_PHRASES):
                        return CaptchaResult(
                            detected=True, 
                            captcha_type="Bol IP Block", details=f"Block phrase detected in {by}={selector}: {text[:120]}",
                            confidence=ConfidenceLevel.HIGH
                        )
                except NoSuchElementException:
                    continue
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                text = body.text.lower()
            except Exception as e:
                body = ""

            if any(phrase in text for phrase in CaptchaPatterns.BOL_BLOCK_PHRASES) or re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text):
                return CaptchaResult(
                    detected=True, 
                    captcha_type="Bol IP Block", details=f"Block phrase detected in body",
                    confidence=ConfidenceLevel.HIGH
                )
        return CaptchaResult(detected=False)
