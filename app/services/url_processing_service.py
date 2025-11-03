from app.models.schemas.processing_results import ProcessingResult
import asyncio
from selenium.common.exceptions import TimeoutException, WebDriverException
from app.services.selenium_manager import SeleniumManager

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

            return ProcessingResult(
                success=True,
                url=url,
                web_title=browser_data["title"],
                html_source=browser_data["page_source"]
            )
        
        except TimeoutException as e:
            return ProcessingResult(
                success=False,
                url=url,
                error_message=f"Timeout Error: {str(e)}"
            )
        except WebDriverException as e:
            return ProcessingResult(
                success=False,
                url=url,
                error_message=f"WebDriver Error: {str(e)}"
            )
        except Exception as e:
            return ProcessingResult(
                success=False,
                url=url,
                error_message=f"Unknown Error: {str(e)}"
            )
    def _execute_browser_job(self, url, selenium_url):
        with SeleniumManager(
            selenium_url=selenium_url,
        ) as driver:
            
            driver.get(url=url)

            return {
                "title": driver.title,
                "page_source": driver.page_source
            }
