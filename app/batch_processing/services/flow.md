## 1. Orchestration (`BatchProcessingOrchestrator`)

- **Batch Initialization**:
  - Notifies the client via `BatchProgressNotifier` that the batch has started, sending the total URL count.
  - Retrieves the necessary `folder_id` from the Multilogin service once (optimization).
- **Concurrent Dispatch**:
  - Uses `task_executor.execute_batch` to schedule `_process_single_url` for every URL in the list.
  - The executor ensures that no more than `max_concurrency` tasks run simultaneously.
- **Result Aggregation**:
  - Collects all results (including exceptions) from the executor.
  - Uses `BatchResultAggregator` to compile final statistics (success/fail counts).
  - Sends the final summary to the client.

## 2. Single URL Workflow (`_process_single_url`)

- **Resource Acquisition**:
  - Asks `ProfileLifecycleManager` for an available profile ID. If none are available (timeout), it fails immediately.
- **Processing**:
  - Delegates to `URLProcessor.process_with_profile`.
- **Feedback Loop**:
  - **Success**: Calls `lifecycle_manager.handle_success` (releases profile) and notifies the client.
  - **Failure/CAPTCHA**: Calls `lifecycle_manager.handle_failure` (burns profile) and sends an error alert.
- **Safety**: Wraps the entire process in a `try/finally` block to ensure `cleanup_on_error` is called if an unexpected crash occurs.

## 3. Browser Logic (`URLProcessor` & `URLProcessingService`)

- **URLProcessor**:
  - Acts as the bridge between the Orchestrator and the lower-level services.
  - Calls `MultiLoginService.start_profile` to get the actual WebSocket Debugger URL (Selenium URL).
  - Passes this URL to the processing service.
- **URLProcessingService**:
  - Executes the actual browser work in a separate thread (`asyncio.to_thread`) to avoid blocking the main async loop.
  - Uses `SeleniumManager` to drive the browser.
  - **Captcha Detection**: Runs the `CaptchaDetector` on the loaded page.
    - If detected: Returns a specific result with `captcha_detected=True`.
    - If clear: Returns the page title and HTML source.

## 4. Progress & Results

- **ProgressNotifier**:
  - Translates domain events (e.g., "url_completed") into standardized WebSocket messages.
- **ResultAggregator**:
  - Converts raw exception objects into safe `ProcessingResult` schemas so the batch doesn't crash on a single failure.
  - Calculates the final success rates for reporting.