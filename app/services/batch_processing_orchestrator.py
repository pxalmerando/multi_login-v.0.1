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
            max_concurrency: int

    ) -> None:
        
        self.multi_login_service = multi_login_service
        self.notifier = notifier
        self.max_concurrency = max_concurrency

        self.url_processor = URLProcessingService()
        self.profile_allocator = ProfileAllocationService(multi_login_service=multi_login_service)

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
            max_concurrent=self.max_concurrency,
            total_urls=urls
        )

        try:
            url_profile_pairs = await self.profile_allocator.pair_urls_with_profile(
                urls=urls,
                max_profiles=self.max_concurrency
            )

            print(f"URL-Profile Pairs: {url_profile_pairs}")

            results = await self._process_with_concurrency(
                url_profile_pairs
            )

            print(f"Batch Results: {results}")

            
            batch_result = self._create_batch_result(
                results=results,
            )


            await self.notifier.notify_batch_completed(
                successful_urls=batch_result.successful_urls,
                failed_urls=batch_result.failed_urls,
                total_urls=batch_result.total_urls
            )

            return batch_result
        except Exception as e:
            await self.notifier.notify_error(f"Batch processing failed: {str(e)}")
            raise


    async def _process_with_concurrency(
            self, 
            url_profile_pairs: List[tuple[str, str]]
    ) -> List[ProcessingResult]:
        
        semaphore = asyncio.Semaphore(
            self.max_concurrency
        )

        async def process_with_semaphore(
                url: str,
                profile_id: str
        ):
            
            
            async with semaphore:
                return await self._process_single_with_profile(
                    url,
                    profile_id
                )
            
        tasks = [
            asyncio.create_task(
                process_with_semaphore(
                    url=url,
                    profile_id=profile_id
                )
            )
            for url, profile_id in url_profile_pairs
        ]

        results = await asyncio.gather(
            *tasks, 
            return_exceptions=True
        )

        processed_results = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                url = url_profile_pairs[i][0]
                processed_results.append(
                    ProcessingResult(
                        success=False,
                        url=url,
                        error_message=str(result),
                    )
                )
            else:
                processed_results.append(
                   result
                )
        print(f"Processed results: {processed_results}")
        print(f"Url profile pairs: {url_profile_pairs}")
        return processed_results
    

    async def _process_single_with_profile(
            self,
            url: str,
            profile_id: str
    ) -> ProcessingResult:
        
        selenium_url = None

        try:
            await self.notifier.notify_processing(
                step=1,
                message=f"Processing URL: {url}",
                total_steps=3
            )

            selenium_url = await self.multi_login_service.start_profile(
                profile_id=profile_id
            )

            print(selenium_url)

            if selenium_url is None:
                return ProcessingResult(
                    success=False,
                    error_message="Failed to start profile",
                    url=url
                )
            
            await self.notifier.notify_processing(
                message=f"Starting profile: {selenium_url}",
                step=2,
                total_steps=3
            )

            await self.notifier.notify_processing(
                message=f"Connecting to browser: {selenium_url}",
                step=3,
                total_steps=3
            )

            result = await self.url_processor.process_url(
                url=url,
                selenium_url=selenium_url
            )


            if result.success:
                await self.notifier.notify_completed(
                    message=f"URL processed successfully",
                    data=result.to_dict()
                )

            return result
        
        except Exception as e:
            if profile_id:
                try:
                    await self.multi_login_service.stop_profile(
                        profile_id=profile_id
                    )
                except Exception as e:
                    print(f"Error stopping profile {profile_id}: {e}")
            return ProcessingResult(
            success=False,
            url=url,
            error_message=str(e)
        )

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