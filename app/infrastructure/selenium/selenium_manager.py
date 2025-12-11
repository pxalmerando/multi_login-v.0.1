from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class SeleniumManager:
    """Handles WebDriver operations"""
    
    def __init__(self, selenium_url: str):
        self.selenium_url = selenium_url
        self.driver = None
    
    def __enter__(self):
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Remote(
            command_executor=self.selenium_url,
            options=options
        )
        return self.driver
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass