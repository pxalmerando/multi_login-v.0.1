
import logging
from typing import List
from app.models.schemas.processing_results import BatchProcessingResult, ProcessingResult

logger = logging.getLogger(__name__)

class BatchResultAggregator:
    """
    Aggregates individual processing results into batch statistics.
    Calculates success rates, failures, and creates summary reports.
    """
    
    @staticmethod
    def create_batch_result(results: List[ProcessingResult]) -> BatchProcessingResult:
        """
        Aggregate individual results into a batch summary.
        """
        successful_urls = sum(1 for r in results if r.success)
        failed_urls = len(results) - successful_urls
        
        logger.info(
            f"[ResultAggregator] Batch complete: "
            f"{successful_urls}/{len(results)} successful"
        )
        
        return BatchProcessingResult(
            total_urls=len(results),
            successful_urls=successful_urls,
            failed_urls=failed_urls,
            results=results
        )
    
    @staticmethod
    def handle_exception_results(
        results: List,
        urls: List[str]
    ) -> List[ProcessingResult]:
        """
        Convert exceptions in results to ProcessingResult objects.
        """
        processed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[ResultAggregator] Exception for {urls[i]}: {result}")
                processed_results.append(
                    ProcessingResult(
                        success=False,
                        url=urls[i],
                        error_message=str(result)
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results