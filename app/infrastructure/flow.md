## 1. Purpose

The Infrastructure layer acts as the **technical foundation** of the application. It isolates external dependencies—such as databases, external APIs, browser automation tools, and real-time sockets—from the core business logic. This ensures that the domain layers (e.g., `batch_processing`, `multilogin`) remain focused on "what" to do, while this layer handles "how" to do it.

## 2. Resource Provisioning

- **On Application Startup**:
  - The layer initializes connection pools for **Redis** (`RedisProfileStorage`) to handle state persistence.
  - It configures the **HTTP Client** (`HttpClient`) with base URLs and timeouts for communicating with the Multilogin API.
  - It prepares the **Selenium Manager** to provision browser instances on demand.

## 3. Service Interaction Flow

When a business service (e.g., `ProfileAllocationService`) needs to perform an action, the flow is as follows:

1.  **Request**: The service calls a high-level method on an infrastructure component (e.g., `storage.acquire_any_available()`).
2.  **Translation**: The infrastructure component translates this domain request into specific technical commands:
    - *Redis*: Executes atomic Lua scripts to manage sets and keys.
    - *Selenium*: Commands the WebDriver to launch a specific profile.
    - *HTTP*: Constructs raw REST requests with appropriate headers and authentication.
3.  **Execution**: The command is executed against the external system.
4.  **Result Mapping**:
    - **Success**: Raw data (JSON, Redis strings) is parsed into Python objects or domain entities.
    - **Failure**: Technical errors (e.g., `httpx.ConnectTimeout`, `redis.ConnectionError`) are caught and logged. They are often re-raised as domain-specific exceptions to allow the application to handle them gracefully (e.g., retrying a batch job).

## 4. Cross-Component Coordination

The infrastructure components are designed to work in concert:

- **Redis & WebSocket**: Redis `pub/sub` or state changes (like profile completion) can trigger `WebSocketNotifier` updates to inform the frontend.
- **Selenium & HTTP**: The `SeleniumManager` often relies on the `HttpClient` to pre-configure profiles (e.g., setting proxies) via API before the browser is actually launched.