## 1. Client Setup

- The `HttpClient` is initialized with a `base_url` (e.g., the Multilogin API endpoint).
- It creates an internal `httpx.AsyncClient` configured with a standard timeout (10 seconds) to prevent hanging requests.

## 2. Request Lifecycle

- **Invocation**: The application calls standard methods like `.get()`, `.post()`, or `.put()`.
- **Preparation**:
  - The full URL is constructed by joining the `base_url` and the endpoint.
  - A standardized `_make_request` method is triggered.

## 3. Execution and Monitoring

- **Observability**:
  - A global counter (`api_call_counts`) increments for the specific method/endpoint pair.
  - A timer starts to measure request latency.
- **Network Call**: The request is sent asynchronously.
- **Logging**:
  - *Success*: Logs the latency and total call count.
  - *Failure*: Logs the error details and the time taken before failure.

## 4. Response Handling

- **Success**: If the status code indicates success (2xx), the JSON body is parsed and returned.
- **Error**:
  - If the status code indicates failure (4xx/5xx), the client attempts to parse the error body.
  - An `HTTPStatusError` is raised, propagating the detailed error context up to the application layer.