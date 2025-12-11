from abc import ABC, abstractmethod
from typing import Protocol
import logging

from app.captcha_detection.models import CaptchaResult


class WebDriverProtocol(Protocol):
    """A protocol that represents the methods and properties of a WebDriver."""

    def get(self, url: str) -> None:
        ...

    def find_element(self, by: str, value: str):
        ...

    def find_elements(self, by: str, value: str):
        ...
    
    @property
    def page_source(self) -> str:
        ...

    @property
    def title(self) -> str:
        ...
    

class DetectionStrategy(ABC):

    def __init__(self, driver: WebDriverProtocol):
        self.driver = driver

    @abstractmethod
    def detect(self) -> CaptchaResult:
        pass

    def _safe_execute(self, detection_func, captcha_type: str) -> CaptchaResult:
        try:
            return detection_func()
        except Exception as e:
            logging.error(f"Error executing during {captcha_type} detection: {e}")
            return CaptchaResult(detected=False)
    

