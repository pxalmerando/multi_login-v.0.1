import asyncio
from fastapi import WebSocket
from selenium .common.exceptions import TimeoutException, WebDriverException
from app.services.multi_login_service import MultiLoginService
from app.services.multi_login_service import SeleniumManager



async def process_url(url: str, processor: MultiLoginService, websocket: WebSocket):

    """
    Process a URL using a MultiLoginService profile.

    Parameters
    ----------
    url : str
        The URL to process.
    processor : MultiLoginService
        The MultiLoginService instance to use for processing the URL.
    websocket : WebSocket
        The WebSocket connection to send updates to.

    Raises
    ------
    TimeoutException
        If the Selenium browser times out while loading the URL.
    WebDriverException
        If an error occurs while connecting to the Selenium browser.
    Exception
        If an unexpected error occurs while processing the URL.

    Returns
    -------
    dict
        A dictionary containing the processed URL data.
    """
    try:
        await websocket.send_json({
            "status": "processing",
            "message": f"Processing URL: {url}",
            "step": 1,
            "total_steps": 4
        })

        selenium_url = await asyncio.to_thread(processor.start_profile)

        if not selenium_url:
            await websocket.send_json({
                "status": "error",
                "message": f"Failed to start profile"
            })
            return

        await websocket.send_json({
            "status": "processing",
            "message": f"Profile started successfully at {selenium_url}",
            "step": 2,
            "total_steps": 4
        })

        await websocket.send_json({
            "status": "processing",
            "message": "Connecting to Selenium browser...",
            "step": 3,
            "total_steps": 4
        })

        def browser_job():

            with SeleniumManager(selenium_url=selenium_url) as driver:
                driver.get(url)
                return {
                    "title": driver.title,
                    "page_source": driver.page_source
                }
        
        results = await asyncio.to_thread(browser_job)


        await websocket.send_json({
            "status": "progress",
            "message": f"Successfully loaded: {results['title']}",
            "step": 4,
            "total_steps": 4
        })

        # Send final data
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

    except (TimeoutException, WebDriverException) as e:
        # Clean up running profile
        processor.PROFILE_RUNNING = [
            p for p in processor.PROFILE_RUNNING if p.get("profile_id") != processor.profile_id
        ]
        await asyncio.to_thread(processor.stop_profile, processor.profile_id)

        await websocket.send_json({
            "status": "error",
            "message": f"Selenium error: {str(e)}"
        })

    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        })









        