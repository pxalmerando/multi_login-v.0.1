## 1. API Communication (`ProfileManager`)

- **Payload Construction**:
  - Centralizes the creation of complex JSON payloads for profile creation/updating.
  - Automatically injects default parameters for "mimic" browsers, OS types, and privacy flags (masking fonts, canvas, WebRTC, etc.).
- **CRUD Operations**:
  - Wraps raw HTTP calls for creating, listing, updating, and deleting profiles.
  - Handles pagination parameters (`limit`, `offset`) when listing profiles.

## 2. Operational Control (`ProfileOperationService`)

- **Concurrency Control**:
  - Maintains a dictionary of `asyncio.Lock` objects, keyed by `profile_id`.
  - This ensures that two workers cannot try to start/stop the *same* profile simultaneously, preventing API race conditions.
- **Start Sequence**:
  - Checks the local registry to see if the profile is already running (reuse).
  - Calls the launcher API endpoint (`/api/v1/profile/.../start`).
  - Parses the response to extract the Selenium port.
  - Registers the active session.
- **Stop Sequence**:
  - Verifies the profile is running.
  - Calls the stop endpoint.
  - Unregisters the session to free memory.

## 3. Session Registry (`ProfileRegistry`)

- **In-Memory Tracking**:
  - Acts as the "source of truth" for what is currently running *on this specific worker instance*.
  - Stores `MultiLoginProfileSession` objects.
  - Uses a lock to ensure thread-safe additions and removals.