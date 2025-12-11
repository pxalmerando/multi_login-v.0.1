import logging
from typing import List, Optional


from app.captcha_detection.models import CaptchaResult
from app.captcha_detection.constants import ConfidenceLevel
from app.captcha_detection.strategies.base import DetectionStrategy
from app.captcha_detection.strategies.generic import GenericDetectionStrategy
from app.captcha_detection.strategies.hcaptcha import HCaptchaDetectionStrategy
from app.captcha_detection.strategies.bol_block import BolBlockDetectionStrategy
from app.captcha_detection.strategies.recaptcha import RecaptchaDetectionStrategy
from app.captcha_detection.strategies.cloudflare import CloudflareDetectionStrategy
from app.captcha_detection.strategies.funcaptcha import FunCaptchaDetectionStrategy
from app.captcha_detection.strategies.url_pattern import URLPatternDetectionStrategy
from app.captcha_detection.strategies.text_pattern import TextPatternDetectionStrategy
from app.captcha_detection.strategies.title_pattern import TitlePatternDetectionStrategy


class CaptchaDetector:

    def __init__(self, driver, strategies: Optional[List[DetectionStrategy]] = None):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.strategies = strategies or self._get_default_strategies()

    def _get_default_strategies(self) -> List[DetectionStrategy]:
        
        return [
            RecaptchaDetectionStrategy(self.driver),
            HCaptchaDetectionStrategy(self.driver),
            CloudflareDetectionStrategy(self.driver),
            FunCaptchaDetectionStrategy(self.driver),
            GenericDetectionStrategy(self.driver),
            URLPatternDetectionStrategy(self.driver),
            TitlePatternDetectionStrategy(self.driver),
            TextPatternDetectionStrategy(self.driver),
            BolBlockDetectionStrategy(self.driver),
        ]
    def detect_captcha(self) -> CaptchaResult:

        results = [strategy.detect() for strategy in self.strategies]

        detected_captchas = [r for r in results if r.detected]

        if detected_captchas:
            best_match = max(
                detected_captchas, 
                key=lambda x: ConfidenceLevel.SCORES.get(x.confidence, 0))
            
            self.logger.info(f"CAPTCHA detected: {best_match.captcha_type} (confidence: {best_match.confidence})")
            return best_match

        self.logger.debug("No CAPTCHA detected")
        return CaptchaResult(detected=False)

    def add_strategy(self, strategy: DetectionStrategy) -> None:
        self.strategies.append(strategy)
        self.logger.debug(f"Added new detection strategy: {strategy.__class__.__name__}")
    
    def remove_strategy(self, strategy: DetectionStrategy) -> None:
        original_count = len(self.strategies)
        self.strategies = [
            s for s in self.strategies 
            if not isinstance(s, strategy)
        ]
        removed_count = original_count - len(self.strategies)
        self.logger.debug(f"Removed {removed_count} strategy(ies) of type: {strategy.__name__}")