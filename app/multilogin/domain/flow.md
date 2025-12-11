## 1. Profile Lifecycle Management

- **Acquisition**:
  - Delegates to the `ProfileAllocator` to find a usable profile.
  - Logs the acquisition for audit purposes.
- **Success Handling**:
  - When a job completes successfully, the manager calls `handle_success`.
  - The profile is **released** back to the pool, making it available for future jobs.
- **Failure Handling**:
  - When a job fails (e.g., due to detection or errors), the manager calls `handle_failure`.
  - The profile is **deleted** (marked as deleted in Redis and removed via API) to prevent reusing a potentially compromised or "burned" profile.
- **Emergency Cleanup**:
  - In case of critical exceptions, `cleanup_on_error` ensures the profile is removed to maintain system hygiene.