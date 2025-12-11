## 1. Session Initialization

- Application invokes the `SeleniumManager` context (using the `with` statement).
- `__enter__` method executes:
  - Configures `ChromeOptions`, adding arguments like `--disable-blink-features=AutomationControlled` for stealth.
  - Establishes a `webdriver.Remote` connection to the specified `selenium_url`.
- Returns the active `driver` instance, ready for browser automation tasks.

## 2. Session Teardown and Cleanup

- Application finishes tasks or encounters an error, triggering the context exit.
- `__exit__` method executes:
  - Verifies if a `driver` instance is currently active.
  - Calls `driver.quit()` to strictly terminate the session on the Selenium Grid and free resources.
  - Wraps the cleanup in a try/except block to ensure the application doesn't crash if the driver is already disconnected.