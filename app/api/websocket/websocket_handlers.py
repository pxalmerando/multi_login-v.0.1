import asyncio
from fastapi import WebSocket
from selenium.common.exceptions import TimeoutException, WebDriverException
from app.services.multi_login_service import MultiLoginService
from app.services.selenium_manager import SeleniumManager
from app.services.multilogin.profile_manager import ProfileManager
from app.services.multilogin.folder_manager import FolderManager

async def process_url(url: str, profile_id: str, websocket: WebSocket, processor: MultiLoginService):
    """
    Process a URL
    Each URL gets its own profile instance.
    """

    try:
        await websocket.send_json({
            "status": "processing",
            "message": f"Processing URL: {url}",
            "step": 1,
            "total_steps": 3
        })

        # Start profile and get Selenium URL
        selenium_url = await processor.start_profile(profile_id=profile_id)

        # Proper None check with explicit comparison
        if selenium_url is None:
            await websocket.send_json({
                "status": "error",
                "message": "Failed to start profile: selenium_url is None"
            })
            return None  # Explicitly return None
        
        # Additional safety check for profile_id
        if profile_id is None:
            await websocket.send_json({
                "status": "error", 
                "message": "Failed to get profile ID"
            })
            return None

        await websocket.send_json({
            "status": "processing",
            "message": f"Profile started successfully at {selenium_url}",
            "step": 2,
            "total_steps": 3
        })

        await websocket.send_json({
            "status": "processing",
            "message": "Connecting to Selenium browser...",
            "step": 3,
            "total_steps": 3
        })

        def browser_job():
            # Added explicit check before using selenium_url
            if selenium_url is None:
                raise ValueError("Selenium URL is None")
                
            with SeleniumManager(selenium_url=selenium_url) as driver:
                driver.get(url)
                return {
                    "title": driver.title,
                    "page_source": driver.page_source
                }
        
        results = await asyncio.to_thread(browser_job)

        # Send completion message
        await websocket.send_json({
            "status": "completed",
            "message": "URL processed successfully.",
            "data": {
                "success": True,
                "url": url,
                "title": results["title"],
                "html_source": results["page_source"]
            }
        })

        return {
            "success": True,
            "url": url,
            "title": results["title"],
            "html_source": results["page_source"]
        }

    except TimeoutException as e:
        error_msg = f"Timeout while processing URL: {str(e)}"
        await handle_error(websocket, error_msg, profile_id, processor)
        return None
    except WebDriverException as e:
        error_msg = f"WebDriver error: {str(e)}"
        await handle_error(websocket, error_msg, profile_id, processor)
        return None
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"Error processing {url}: {error_msg}")
        await handle_error(websocket, error_msg, profile_id, processor)
        return None

async def handle_error(websocket: WebSocket, error_msg: str, profile_id: str, processor: MultiLoginService):
    """Helper function to handle errors consistently"""
    await websocket.send_json({
        "status": "error",
        "message": error_msg
    })
    
    # Only stop profile if we have a valid profile_id
    if profile_id:
        try:
            await processor.stop_profile(profile_id)
        except Exception as e:
            print(f"Error stopping profile {profile_id}: {e}")

async def process_multiple_urls(urls: list[str],websocket: WebSocket, processor: MultiLoginService, max_concurrent: int = 3):

    """Process multiple URLs with concurrency control"""
    folder_id = await processor.folder_manager.get_folder_ids()
    folder_id = folder_id[0]
    profile_ids = await processor.profile_manager.get_profile_ids(
        folder_id=folder_id
    )
    # Validate input
    if not urls:
        await websocket.send_json({
            "status": "error",
            "message": "No URLs provided"
        })
        return []

    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_semaphore(url: str, profile_id: str):
        async with semaphore:
            return await process_url(
                url=url,
                profile_id=profile_id,
                websocket=websocket,
                processor=processor
            )
        
    await websocket.send_json({
        "status": "batch_started",
        "message": f"Processing {len(urls)} URLs (max {max_concurrent} concurrent)",
        "total_urls": len(urls)
    })

    tasks = [asyncio.create_task(process_with_semaphore(url=url, profile_id=profile_id)) for url, profile_id in zip(urls, profile_ids)]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Count successful and failed processing
    successful = 0
    failed = 0
    
    for result in results:
        if isinstance(result, Exception):
            failed += 1
            # Log the exception but don't send via websocket to avoid spam
            print(f"URL processing failed: {str(result)}")
        elif result is not None:  # Only count non-None results as successful
            successful += 1

    await websocket.send_json({
        "status": "batch_completed",
        "message": f"Batch complete: {successful} successful, {failed} failed",
        "total_urls": len(urls),
        "successful": successful,
        "failed": failed
    })
    
    return [r for r in results if not isinstance(r, Exception) and r is not None]