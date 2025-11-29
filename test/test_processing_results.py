import pytest
from app.models.schemas.processing_results import ProcessingResult, BatchProcessingResult
from datetime import datetime

class TestProcessingResult:
    
    def test_processing_result_success(self):
        """Test successful processing result"""
        
        result = ProcessingResult(
            success=True,
            url="https://example.com",
            web_title="Test Page"
        )
        
        
        assert result.success is True
        assert result.url == "https://example.com"
        assert result.web_title == "Test Page"
        assert result.processed_at is not None
    
    def test_processing_result_failure(self):
        """Test failed processing result"""
        
        result = ProcessingResult(
            success=False,
            url="https://example.com",
            error_message="Connection timeout"
        )
        
        
        assert result.success is False
        assert result.error_message == "Connection timeout"
    
    def test_processing_result_to_dict(self):
        """Test converting result to dictionary"""
        
        result = ProcessingResult(
            success=True,
            url="https://example.com",
            web_title="Test"
        )
        
        
        result_dict = result.to_dict()
        
        
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["url"] == "https://example.com"
        assert "processed_at" in result_dict

class TestBatchProcessingResult:
    
    def test_batch_processing_result(self):
        """Test batch processing result creation"""
        
        results = [
            ProcessingResult(success=True, url="https://example.com"),
            ProcessingResult(success=False, url="https://test.com", error_message="Error")
        ]
        
        
        batch_result = BatchProcessingResult(
            total_urls=2,
            successful_urls=1,
            failed_urls=1,
            results=results
        )
        
        
        assert batch_result.total_urls == 2
        assert batch_result.successful_urls == 1
        assert batch_result.failed_urls == 1
        assert len(batch_result.results) == 2
    
    def test_batch_result_to_dict(self):
        """Test converting batch result to dictionary"""
        
        results = [
            ProcessingResult(success=True, url="https://example.com")
        ]
        batch_result = BatchProcessingResult(
            total_urls=1,
            successful_urls=1,
            failed_urls=0,
            results=results
        )
        
        
        result_dict = batch_result.to_dict()
        
        
        assert isinstance(result_dict, dict)
        assert result_dict["total_urls"] == 1
        assert len(result_dict["results"]) == 1