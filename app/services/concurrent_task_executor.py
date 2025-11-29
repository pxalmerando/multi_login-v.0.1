
import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)

class ConcurrentTaskExecutor:
    """
    Executes tasks concurrently while respecting rate limits.
    Manages semaphores and task coordination.
    """
    
    def __init__(self, max_concurrency: int):
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    async def execute_batch(
        self,
        items: List,
        processor_func
    ) -> List:
        """
        Execute a batch of tasks concurrently.
        
        Args:
            items: List of items to process
            processor_func: Async function to process each item
        
        Returns:
            List of results (may include exceptions)
        """
        async def execute_with_limit(item):
            async with self.semaphore:
                return await processor_func(item)
        
        tasks = [execute_with_limit(item) for item in items]
        
        logger.info(
            f"[TaskExecutor] Executing {len(tasks)} tasks "
            f"(max concurrent: {self.max_concurrency})"
        )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results