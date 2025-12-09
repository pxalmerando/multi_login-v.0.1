import asyncio
import logging
import typing
from app.batch_processing.schemas import ProcessingResult
from app.services.captcha_detection.models import CaptchaResult
from app.batch_processing.exceptions import map_exception_to_message
from app.services.captcha_detection.detector import CaptchaDetector
from app.batch_processing.services.selenium_manager import SeleniumManager

logger = logging.getLogger(__name__)
class URLProcessingService:

    async def process_url(
            self,
            url: str,
            selenium_url: str
    ) -> ProcessingResult:
        try:
            browser_data = await asyncio.to_thread(
                self._execute_browser_job,
                url, 
                selenium_url
            )
            if browser_data.get("captcha_detected"):
                captcha_result = typing.cast(CaptchaResult, browser_data["captcha_result"])
                return ProcessingResult(
                    success=False,
                    captcha_detected=True,
                    url=url,
                    error_message=f"CAPTCHA Detected: {captcha_result.captcha_type}",
                    metadata={
                        "captcha_type": captcha_result.captcha_type,
                        "captcha_details": captcha_result.details,
                        "captcha_confidence": captcha_result.confidence
                    }
                )
            return ProcessingResult(
                success=True,
                url=url,
                web_title=browser_data["title"],
                html_source=browser_data["page_source"]
            )
        except Exception as e:
            return ProcessingResult(
                success=False,
                url=url,
                error_message=map_exception_to_message(e)
            )
        
    def _execute_browser_job(self, url, selenium_url):
        with SeleniumManager(
            selenium_url=selenium_url,
        ) as driver:
            driver.get(url=url)
            try:
                captcha_detector = CaptchaDetector(driver=driver)
                captcha_result = captcha_detector.detect_captcha()
                if captcha_result.detected:
                    print(
                        f"CAPTCHA detected on {url}: {captcha_result.captcha_type} (confidence: {captcha_result.confidence})"
                    )
                    return {
                        "captcha_detected": True,
                        "captcha_result": captcha_result
                    }
            except Exception as e:
                logger.exception(f"Error during CAPTCHA detection: {e}")
                pass
            return {
                "title": driver.title,
                "page_source": driver.page_source
            }