## 1. Service Orchestration (`MultiLoginService`)

- **Initialization**:
  - The service lazy-loads its dependencies (`FolderManager`, `ProfileManager`) only when first needed.
  - It authenticates with the Multilogin API to obtain an access token, which is then stored in `self.headers`.
- **Façade Pattern**:
  - It provides a simplified interface (`start_profile`, `stop_profile`, `delete_profile`) that hides the complexity of the underlying infrastructure components.
  - For example, `start_profile` ensures the service is initialized, validates inputs, and then delegates to `ProfileOperationService`.

## 2. Allocation Strategy (`ProfileAllocationService`)

- **Double-Checked Locking**:
  - Uses `asyncio.Lock` and a boolean flag (`_initial_fetch_done`) to ensure that the expensive "fetch all profiles" operation happens exactly once, even with multiple concurrent workers.
- **Acquisition Loop**:
  - Tries to get an available profile from Redis (`storage.acquire_any_available()`).
  - If the pool is empty:
    - Checks if it can create a new profile (if `current_total < max_profiles`).
    - Creates a new profile via the repository.
    - Adds it to the Redis pool using the atomic `add_profile_if_under_limit` script.
  - If the pool is full and everything is busy, it waits (sleeps) and retries until the `timeout` is reached.

## 3. Session Cleanup (`SessionCleanupService`)

- **Batch Termination**:
  - Iterates through all locally registered sessions in `ProfileRegistry`.
  - Attempts to stop each one via `ProfileOperationService`.
  - Aggregates failures but ensures the registry is cleared at the end to prevent memory leaks.