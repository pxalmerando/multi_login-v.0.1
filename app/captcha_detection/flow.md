# Captcha Detection – Flow Overview

## 1. What this module does

- Detects if a page is showing a CAPTCHA or block screen (reCAPTCHA, hCaptcha, Cloudflare, FunCaptcha, generic, BOL block, etc.).
- Uses Selenium-like WebDriver to inspect URL, HTML, text, and title.
- Combines results from multiple strategies and returns the best match as a `CaptchaResult`.

---

## 2. Core components

- `CaptchaResult` (models.py)
  - Fields like: `detected: bool`, `captcha_type: str`, `confidence: str`, optional extra metadata.
- `ConfidenceLevel` (constants.py)
  - Named levels: `HIGH`, `MEDIUM`, `LOW`, `NONE`.
  - `SCORES` mapping to numeric values to compare results.
- `CaptchaPatterns` (constants.py)
  - Domain lists for each type (reCAPTCHA, hCaptcha, Cloudflare, FunCaptcha, BOL).
  - CSS/XPath selectors for known widgets.
  - URL, title, and text patterns used by pattern-based strategies.

---

## 3. DetectionStrategy base

- `WebDriverProtocol` (strategies/base.py)
  - Abstracts the WebDriver methods used:
    - `get(url)`, `find_element`, `find_elements`.
    - Properties: `page_source`, `title`.
- `DetectionStrategy` (strategies/base.py)
  - Base class for all strategies; holds `self.driver`.
  - `detect(self) -> CaptchaResult` (abstract).
  - `_safe_execute(detection_func, captcha_type)`:
    - wraps a strategy’s logic in try/except.
    - logs errors and returns `CaptchaResult(detected=False)` on failure.

---

## 4. Individual strategies (strategies/)

Each strategy inspects the current page in a different way and returns a `CaptchaResult`:

- `RecaptchaDetectionStrategy`
  - Checks `CaptchaPatterns.RECAPTCHA_DOMAINS` and `RECAPTCHA_SELECTORS`.
- `HCaptchaDetectionStrategy`
  - Checks `HCAPTCHA_DOMAINS` and corresponding selectors.
- `CloudflareDetectionStrategy`
  - Uses `CLOUDFLARE_DOMAINS`, `CLOUDFLARE_KEYWORDS`, `CLOUDFLARE_SELECTORS`.
- `FunCaptchaDetectionStrategy`
  - Uses `FUNCAPTCHA_DOMAINS` patterns.
- `GenericDetectionStrategy`
  - Searches for generic CAPTCHA-related selectors / keywords.
- `URLPatternDetectionStrategy`
  - Checks current URL against `URL_PATTERNS`.
- `TitlePatternDetectionStrategy`
  - Checks page title against `TITLE_PATTERNS`.
- `TextPatternDetectionStrategy`
  - Scans page text for `TEXT_PATTERNS`.
- `BolBlockDetectionStrategy`
  - Uses `BOL_DOMAINS`, `BOL_BLOCK_PHRASES`, `BOL_BLOCK_SELECTORS` to detect BOL-specific blocks.

---

## 5. CaptchaDetector orchestration

- `CaptchaDetector(driver, strategies=None)` (detector.py)
  - Stores `driver` and a logger.
  - If no custom `strategies` are passed, builds a default ordered list:
    - Recaptcha, HCaptcha, Cloudflare, FunCaptcha, Generic,
      URLPattern, TitlePattern, TextPattern, BolBlock.
- `detect_captcha() -> CaptchaResult`
  - Calls `strategy.detect()` for each strategy.
  - Collects all `CaptchaResult` objects.
  - Filters to only `detected == True`.
  - If any detected:
    - picks the one with highest `ConfidenceLevel.SCORES[confidence]`.
    - logs: `CAPTCHA detected: {captcha_type} (confidence: {confidence})`.
    - returns that best match.
  - If none detected:
    - logs “No CAPTCHA detected”.
    - returns `CaptchaResult(detected=False)`.
- Strategy management
  - `add_strategy(strategy)`
    - appends a new strategy instance to the list.
  - `remove_strategy(strategy_type)`
    - removes strategies that are instances of the given type.
    - logs how many were removed.

---

## 6. Typical usage

- Instantiate with a Selenium WebDriver (or compatible object):
  - `detector = CaptchaDetector(driver)`
- After loading a page with the driver:
  - `result = detector.detect_captcha()`
- Use `result` to decide:
  - whether to trigger a CAPTCHA solver,
  - change proxy / profile,
  - or continue normal automation.