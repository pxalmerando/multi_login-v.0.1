## 1. Client connects and authenticates (WebSocket)

- Client connects to `/ws/process_urls` with a JWT `token` query parameter.
- Server:
  - decodes and verifies the JWT
  - extracts the user email (`sub`)
  - accepts the WebSocket and sends a “connected” message with the email
- Then it initializes:
  - RedisProfileStorage
  - MultiLoginService
  - ProfileRepository
  - ProfileAllocationService

## 2. WebSocket handler wires the batch feature

- Validates the request.
- Builds batch components:
  - URLProcessor (uses MultiLoginService + URLProcessingService)
  - BatchProgressNotifier (wraps WebSocketNotifier)
  - BatchResultAggregator
  - ConcurrentTaskExecutor (with max_concurrency)
  - ProfileLifecycleManager
- Creates BatchProcessingOrchestrator with these dependencies.
- Calls `orchestrator.process_batch(urls)`.

## 3. Orchestrator processes URLs concurrently

- Notifies batch start via BatchProgressNotifier.
- Uses ConcurrentTaskExecutor to run `_process_single_url` for each URL.
- `_process_single_url`:
  - acquires a profile from ProfileLifecycleManager
  - notifies URL start
  - calls `URLProcessor.process_with_profile(url, profile_id, folder_id)`
  - based on result:
    - marks profile success/failure (including CAPTCHA)
    - sends progress/error notifications
  - returns a `ProcessingResult` for the URL.

## 4. Aggregation and final notification

- ConcurrentTaskExecutor returns a list of results or exceptions.
- BatchResultAggregator:
  - converts exceptions into `ProcessingResult`
  - builds a `BatchProcessingResult` (totals + list of per-URL results).
- Orchestrator:
  - notifies batch complete via BatchProgressNotifier (success/failed).
  - returns the `BatchProcessingResult` to the WebSocket handler.

## 5. WebSocket response

- Handler sends final batch summary to the client using WebSocketNotifier.