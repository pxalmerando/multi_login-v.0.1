from selenium.webdriver.common.by import By


class ConfidenceLevel:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

    SCORES = {
        HIGH: 3,
        MEDIUM: 2,
        LOW: 1,
        NONE: 0
    }

class CaptchaPatterns:

    RECAPTCHA_DOMAINS = ["google.com/recaptcha"]
    RECAPTCHA_SELECTORS = [
        (By.CLASS_NAME, "g-recaptcha"),
        (By.CLASS_NAME, "grecaptcha-badge"),
        (By.ID, "recaptcha")
    ]
    
    HCAPTCHA_DOMAINS = ["hcaptcha.com"]
    HCAPTCHA_SELECTORS = [(By.CLASS_NAME, "h-captcha")]
    
    CLOUDFLARE_DOMAINS = ["challenges.cloudflare.com", "cloudflare.com/turnstile"]
    CLOUDFLARE_KEYWORDS = ["challenge", "checking your browser"]
    CLOUDFLARE_SELECTORS = [
        (By.ID, "cf-challenge-running"),
        (By.CLASS_NAME, "cf-challenge-running")
    ]
    
    FUNCAPTCHA_DOMAINS = ["arkoselabs.com", "funcaptcha.com", "arkose"]
    
    GENERIC_SELECTORS = [
        "captcha", "captcha-container", "captcha-box",
        "verification", "bot-detection", "human-verification"
    ]
    
    URL_PATTERNS = [
        "captcha", "challenge", "verify", "recaptcha",
        "hcaptcha", "bot-check", "human-verification"
    ]
    
    TITLE_PATTERNS = [
        "just a moment", "verify you are human", "please verify",
        "security check", "captcha", "bot verification", "are you a robot"
    ]
    
    TEXT_PATTERNS = [
        "verify you are human", "prove you are not a robot",
        "complete the captcha", "solve the puzzle",
        "security check required", "unusual traffic from your network",
        "automated access", "select all images", "click to verify"
    ]

    