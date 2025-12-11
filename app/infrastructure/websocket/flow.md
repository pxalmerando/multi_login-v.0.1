## 1. Notification Wrapper Initialization

- The `WebSocketNotifier` is initialized by wrapping an active, open `WebSocket` connection.
- It relies on the `NotificationStatus` Enum to strictly type the kinds of messages sent (e.g., `BATCH_STARTED`, `PROCESSING`, `ERROR`), ensuring protocol consistency.

## 2. Standardized Message Construction

- The core `send_status` method constructs a uniform JSON payload:
  - **Status**: The string value from the Enum.
  - **Message**: A human-readable description.
  - **Data**: (Optional) A dictionary of payload results.
  - **Progress**: (Optional) Current `step` and `total_steps` for UI progress bars.

## 3. specialized Notification Flows

- **Batch Lifecycle**:
  - `notify_batch_started`: Sends the total URL count and concurrency settings.
  - `notify_batch_completed`: Sends the final tally of successful vs. failed URLs.
- **Real-time Progress**:
  - `notify_processing`: Continuously updates the client with the current step number inside a loop.
- **Error Reporting**:
  - `notify_error`: Sends immediate alerts if a process fails, allowing the frontend to react without closing the socket.