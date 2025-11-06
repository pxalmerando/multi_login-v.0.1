from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from app.services.captcha_detection.strategies.base import DetectionStrategy
from app.services.captcha_detection.models import CaptchaResult
from app.services.captcha_detection.constants import CaptchaPatterns, ConfidenceLevel

class CloudflareDetectionStrategy(DetectionStrategy):

    def detect(self) -> CaptchaResult:
        return self._safe_execute(self._check_cloudflare, "Cloudflare")

    def _check_cloudflare(self) -> CaptchaResult:
        result = self._check_page_source()

        if result.detected:
            return result
        
        result = self._check_iframes()

        if result.detected:
            return result
        
        return self._check_dom_elements()
    
    def _check_page_source(self) -> CaptchaResult:
        page_source = self.driver.page_source.lower()

        if "cloudflare" in page_source and any(term in page_source for term in CaptchaPatterns.CLOUDFLARE_KEYWORDS):
            return CaptchaResult(
                detected=True,
                captcha_type="Cloudflare CAPTCHA",
                details="Detected Cloudflare CAPTCHA via page source analysis.",
                confidence=ConfidenceLevel.HIGH
            )
        return CaptchaResult(detected=False)
    
    def _check_iframes(self) -> CaptchaResult:
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

        for iframe in iframes:
            src = iframe.get_attribute("src") or ""

            if any(domain in src for domain in CaptchaPatterns.CLOUDFLARE_DOMAINS):
                return CaptchaResult(
                    detected=True,
                    captcha_type="Cloudflare CAPTCHA",
                    details="Detected Cloudflare CAPTCHA via iframe source analysis.",
                    confidence=ConfidenceLevel.MEDIUM
                )
            
        return CaptchaResult(detected=False)

    def _check_dom_elements(self) -> CaptchaResult:
        for by, value in CaptchaPatterns.CLOUDFLARE_SELECTORS:
            try:
                self.driver.find_element(by, value)
                return CaptchaResult(
                    detected=True,
                    type="Cloudflare Challenge",
                    details=f"Found Cloudflare element with {by}: {value}",
                    confidence=ConfidenceLevel.HIGH
                )
            except NoSuchElementException:
                continue
        
        return CaptchaResult(detected=False)