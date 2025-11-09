import asyncio
from typing import List
from app.models.schemas.processing_results import ProcessingResult, BatchProcessingResult
from app.services.url_processing_service import URLProcessingService
from app.services.profile_allocation_service import ProfileAllocationService
from app.services.multi_login_service import MultiLoginService
from app.adapters.websocket_notifier import WebSocketNotifier
class BatchProcessingOrchestrator:
    def __init__(
            self,
            multi_login_service: MultiLoginService,
            notifier: WebSocketNotifier,
            max_concurrency: int,
            profile_allocator: ProfileAllocationService
    ) -> None:
        
        self.multi_login_service = multi_login_service
        self.notifier = notifier
        self.max_concurrency = max_concurrency
        self.url_processor = URLProcessingService()
        self.profile_allocator = profile_allocator
    async def process_batch(self, urls: List[str]):
        if not urls:
            await self.notifier.notify_error("No URLs provided")
            return BatchProcessingResult(
                failed_urls=0,
                successful_urls=0,
                total_urls=0,
                results=[]
            )
        
        await self.notifier.notify_batch_started(
            total_urls=len(urls),
            max_concurrent=self.max_concurrency
        )
        try:
            folder_id = await self.multi_login_service.get_folder_id()
            results = await self._process_with_jit_allocation(
                urls=urls,
                folder_id=folder_id
            )
            batch_result = self._create_batch_result(
                results=results,
            )
            await self.notifier.notify_batch_completed(
                successful_urls=batch_result.successful_urls,
                total_urls=batch_result.total_urls,
                failed_urls=batch_result.failed_urls
            )
            print(f"Batch processing completed. {batch_result.successful_urls} URLs processed successfully. {batch_result.failed_urls} URLs failed to process.")
            print(f"Batch processing completed. {batch_result.successful_urls} URLs processed successfully. {batch_result.failed_urls} URLs failed to process.")
            return batch_result
        except Exception as e:
            await self.notifier.notify_error(f"Batch processing failed: {str(e)}")
            raise
    async def _process_with_jit_allocation(
        self, 
        urls: List[str],
        folder_id: str
    ) -> List[ProcessingResult]:
        
        semaphore = asyncio.Semaphore(self.max_concurrency)
        async def process_single_url(url: str):
            profile_id = None
            async with semaphore:
                try:
                    profile_id = await self.profile_allocator.acquire_profile(
                        folder_id=folder_id
                    )
                    
                    print(f"Assigned profile {profile_id} to URL: {url}")
                    
                    result = await self._process_single_with_profile(url, profile_id)

                    if not result.captcha_detected:
                        await self.profile_allocator.release_profile(profile_id)

                    return result
                    
                    
                except Exception as e:

                    if profile_id:
                        await self.profile_allocator.release_profile(profile_id)
                    return ProcessingResult(
                        success=False,
                        url=url,
                        error_message=f"Failed to allocate profile: {str(e)}"
                    )
        
        tasks = [process_single_url(url) for url in urls]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ProcessingResult(
                        success=False,
                        url=urls[i],
                        error_message=str(result),
                    )
                )
            else:
                processed_results.append(result)
                
        return processed_results
    
    async def _process_single_with_profile(
        self,
        url: str,
        profile_id: str
    ) -> ProcessingResult:
        selenium_url = None
        profile_should_be_deleted = False
        try:
            await self.notifier.notify_processing(
                step=1,
                message=f"Processing URL: {url}",
                total_steps=3
            )
            selenium_url = await self.multi_login_service.start_profile(profile_id)
            if selenium_url is None:
                await self.profile_allocator.mark_profile_deleted(profile_id)
                return ProcessingResult(
                    success=False,
                    error_message="Failed to start profile",
                    url=url
                )
            await self.notifier.notify_processing(
                message=f"Starting profile: {selenium_url}", step=2, total_steps=3
            )
            await self.notifier.notify_processing(
                message=f"Connecting to browser: {selenium_url}", step=3, total_steps=3
            )
            result = await self.url_processor.process_url(url=url, selenium_url=selenium_url)
            if result.captcha_detected:
                await self.notifier.notify_error(f"CAPTCHA detected for URL: {url}")
                profile_should_be_deleted = True
                
                try:
                    await self.multi_login_service.stop_profile(profile_id)
                except:
                    pass
                try:
                    await self.multi_login_service.delete_profile(profile_id)
                except:
                    pass
                
                
                await self.profile_allocator.mark_profile_deleted(profile_id)
                return result
            
            if result.success:
                await self.notifier.notify_completed(
                    message="URL processed successfully",
                    data=result.to_dict()
                )
            return result
        except Exception as e:
            profile_should_be_deleted = True
            try:
                await self.multi_login_service.stop_profile(profile_id)
            except:
                pass
            return ProcessingResult(success=False, url=url, error_message=str(e))
        finally:
            
            if not profile_should_be_deleted:
                await self.profile_allocator.release_profile(profile_id)
    def _create_batch_result(
            self,
            results: List[ProcessingResult]
    ) -> BatchProcessingResult:
        
        successful_urls = sum(1 for r in results if r.success)
        failed_urls = len(results) - successful_urls
        return BatchProcessingResult(
            total_urls=len(results),
            successful_urls=successful_urls,
            failed_urls=failed_urls,
            results=results
        )