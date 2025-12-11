import pytest
import asyncio

from app.utils.concurrent_task_executor import ConcurrentTaskExecutor

class TestConcurrentTaskExecutor:
    """Test ConcurrentTaskExecutor - manages concurrent execution with rate limiting"""
    
    @pytest.fixture
    def task_executor(self):
        return ConcurrentTaskExecutor(max_concurrency=3)
    
    @pytest.mark.asyncio
    async def test_execute_batch_respects_concurrency_limit(self, task_executor):
        """Test that concurrency limit is respected"""
        processing_times = []
        max_concurrent = [0]
        current_concurrent = [0]
        
        async def mock_processor(item):
            
            current_concurrent[0] += 1
            max_concurrent[0] = max(max_concurrent[0], current_concurrent[0])
            
            
            await asyncio.sleep(0.1)
            processing_times.append(asyncio.get_event_loop().time())
            
            current_concurrent[0] -= 1
            return f"processed_{item}"
        
        
        items = list(range(10))  
        results = await task_executor.execute_batch(items, mock_processor)
        
        
        assert max_concurrent[0] <= 3  
        assert len(results) == 10
        assert all(r.startswith("processed_") for r in results)

    @pytest.mark.asyncio
    async def test_execute_batch_handles_exceptions(self, task_executor):
        """Test that exceptions in tasks are handled gracefully"""
        async def mock_processor(item):
            if item == 2:
                raise Exception("Simulated failure")
            return f"success_{item}"
        
        
        items = [0, 1, 2, 3]
        results = await task_executor.execute_batch(items, mock_processor)
        
        
        assert len(results) == 4
        assert results[0] == "success_0"
        assert results[1] == "success_1"
        assert isinstance(results[2], Exception)
        assert "Simulated failure" in str(results[2])
        assert results[3] == "success_3"

    @pytest.mark.asyncio
    async def test_execute_batch_empty(self, task_executor):
        """Test executing empty batch"""
        async def mock_processor(item):
            return f"processed_{item}"
        
        
        results = await task_executor.execute_batch([], mock_processor)
        
        
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_batch_single_item(self, task_executor):
        """Test executing single item"""
        async def mock_processor(item):
            await asyncio.sleep(0.01)
            return item * 2
        
        
        results = await task_executor.execute_batch([5], mock_processor)
        
        
        assert results == [10]