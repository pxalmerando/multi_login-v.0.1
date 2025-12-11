## 1. Connection and Authentication

- Client initiates a WebSocket connection to `/ws/process_urls`, providing a JWT `token`.
- **Validation**:
  - The server attempts to decode the token using the application's `SECRET_KEY`.
  - If the token is missing, invalid, or expired, the socket is closed immediately with a specific error code (e.g., 4001, 1008).
- **Handshake**:
  - Upon successful validation, the server extracts the user's email (`sub`).
  - It accepts the connection and sends a `connected` JSON status message to the client.

## 2. Resource Initialization

- Once connected, the server initializes the dedicated infrastructure for this session:
  - **Redis Storage**: Connects to the Redis backend (`RedisProfileStorage`) to track profile states.
  - **MultiLogin Service**: Initializes the connection to the MultiLogin API.
  - **Allocator**: Wires up the `ProfileAllocationService` with the repository and storage layers.

## 3. Message Handling Loop

- The server enters a continuous listener loop:
  - **Receive**: Awaits a JSON message containing a `urls` list from the client.
  - **Validate**: Checks if the input is a valid non-empty list of strings. If invalid, it sends an error message back and waits for the next request.
  - **Process**: Passes valid URLs to `process_multiple_urls`. This function drives the batch processing logic while using the open WebSocket to stream progress updates back to the client.

## 4. Disconnection and Cleanup

- **Trigger**: The loop breaks if the client disconnects (`WebSocketDisconnect`) or an unexpected exception occurs.
- **Safe Teardown**:
  - The `finally` block ensures critical cleanup runs regardless of how the session ended.
  - `redis_storage.flush()`: Clears temporary profile locks or keys associated with this session.
  - `multi_login_service.cleanup()`: Releases any held browser profiles or resources to prevent leaks.