from selenium.common.exceptions import TimeoutException, WebDriverException

def map_exception_to_message(e: Exception):
    if isinstance(e, TimeoutException):
        return f"Timeout Error: {e}"
    if isinstance(e, WebDriverException):
        return f"Webdriver Error: {e}"
    return f"Unknown Error: {e}"