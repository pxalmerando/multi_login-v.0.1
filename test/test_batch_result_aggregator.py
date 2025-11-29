from app.models.schemas.processing_results import ProcessingResult
from app.services.batch_result_aggregator import BatchResultAggregator

class TestBatchResultAggregator:
    """Test BatchResultAggregator - calculates batch statistics and summaries"""
    
    def test_create_batch_result_all_successful(self):
        """Test aggregating all successful results"""
        
        results = [
            ProcessingResult(success=True, url="https://example1.com"),
            ProcessingResult(success=True, url="https://example2.com"),
            ProcessingResult(success=True, url="https://example3.com")
        ]
        
        
        batch_result = BatchResultAggregator.create_batch_result(results)
        
        
        assert batch_result.total_urls == 3
        assert batch_result.successful_urls == 3
        assert batch_result.failed_urls == 0
        assert batch_result.results == results

    def test_create_batch_result_mixed_success(self):
        """Test aggregating mixed success/failure results"""
        
        results = [
            ProcessingResult(success=True, url="https://example1.com"),
            ProcessingResult(success=False, url="https://example2.com", error_message="Timeout"),
            ProcessingResult(success=True, url="https://example3.com"),
            ProcessingResult(success=False, url="https://example4.com", error_message="CAPTCHA")
        ]
        
        
        batch_result = BatchResultAggregator.create_batch_result(results)
        
        
        assert batch_result.total_urls == 4
        assert batch_result.successful_urls == 2
        assert batch_result.failed_urls == 2

    def test_create_batch_result_empty(self):
        """Test aggregating empty results list"""
        
        batch_result = BatchResultAggregator.create_batch_result([])
        
        
        assert batch_result.total_urls == 0
        assert batch_result.successful_urls == 0
        assert batch_result.failed_urls == 0
        assert batch_result.results == []

    def test_handle_exception_results_converts_exceptions(self):
        """Test converting exceptions to ProcessingResult objects"""
        
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        results = [
            ProcessingResult(success=True, url="https://example1.com"),
            Exception("Network timeout"),
            ProcessingResult(success=False, url="https://example3.com", error_message="CAPTCHA")
        ]
        
        
        processed_results = BatchResultAggregator.handle_exception_results(results, urls)
        
        
        assert len(processed_results) == 3
        assert processed_results[0].success is True
        assert processed_results[1].success is False
        assert "Network timeout" in processed_results[1].error_message
        assert processed_results[1].url == "https://example2.com"
        assert processed_results[2].success is False

    def test_handle_exception_results_all_successful(self):
        """Test handling when no exceptions occur"""
        
        urls = ["https://example1.com", "https://example2.com"]
        results = [
            ProcessingResult(success=True, url="https://example1.com"),
            ProcessingResult(success=True, url="https://example2.com")
        ]
        
        
        processed_results = BatchResultAggregator.handle_exception_results(results, urls)
        
        
        assert processed_results == results