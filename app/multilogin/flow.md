# MultiLogin Auth, Profile, Folder & Proxy – Flow Overview

## 1. Authentication & Token Flow

**Layer:** `MultiLoginAuthService` (Infrastructure/Auth)

- **Entry Point:** `MultiLoginAuthService.get_access_token()`
  - Calls `RedisTokenManager.get_tokens()`
  
- **Token Manager Logic** (Internal Flow):
  - `TokenService` attempts to load tokens from Redis via `TokenRepository`.
    - `TokenValidator` checks required fields and expiration.
  - **If valid:** Returns cached tokens immediately.
  - **If invalid/missing:**
    - `UserAuth` executes login logic (`email`/`password` from config).
    - `POST /user/signin` to MultiLogin API.
    - Extracts `access_token` and `refresh_token`.
    - `TokenRepository` saves new tokens to Redis.

## 2. Profile Management Flow (CRUD)

**Layer:** `ProfileRepository` → `ProfileManager` (Infrastructure)

- **Create Profile**: `ProfileRepository.create_profile(folder_id, name)`
  - Calls `ProfileManager.create_profile`
    - Builds payload via `_build_profile_payload` using defaults:
      - `browser_type`: "mimic", `os_type`: "windows"
      - `parameters`: Includes default masking flags (audio, canvas, fonts, etc.) and local storage settings.
      - `proxy`: If provided, sets `proxy_masking` to "custom".
    - `POST /profile/create`
  - Extracts and returns the new `profile_id` from response `ids` list.

- **List Profiles**: `ProfileRepository.fetch_all_profiles(folder_id)`
  - Calls `ProfileManager.get_profile_ids`
    - `POST /profile/search` (Payload: `{folder_id, limit, offset...}`)
    - Extracts `id` field from the resulting profile list.

- **Delete Profile**: `ProfileRepository.delete_profile(profile_id)`
  - Calls `ProfileManager.delete_profile`
    - `POST /profile/remove`
    - Payload: `{ ids: [profile_id], permanently: True }`

## 3. Folder Management Flow

**Layer:** `FolderManager` (Infrastructure)

- `FolderManager.get_or_create_default_folder(folder_name)`
  - **Cache Check:** Checks in-memory `_folder_id_cache`. If present, return immediately.
  - **Fetch Existing:** Calls `get_folder_ids()` (`GET /workspace/folders`).
    - If folders exist, cache and return the first ID.
  - **Create New:** If no folders exist:
    - Calls `create_folder(folder_name)` (`POST /workspace/folder_create`).
    - Extracts new ID, caches it, and returns it.

## 4. Profile Lifecycle & Operations (Start/Stop)

**Layer:** `ProfileOperationService` (Application) → `ProfileRegistry` (State)

- **Start Profile**: `ProfileOperationService.start_profile(profile_id, folder_id, headers)`
  1. **Locking:** Acquires an `asyncio.Lock` specific to the `profile_id`.
  2. **Registry Check:** Checks `ProfileRegistry` to see if session already exists.
     - If yes, return existing `selenium_url`.
  3. **API Call:**
     - `GET /api/v1/profile/f/{folder_id}/p/{profile_id}/start?automation_type=selenium`
  4. **Response Parsing:**
     - `parse_profile_start_response` validates status code (200 OK).
     - Maps JSON response to `MultiLoginProfileSession` object.
  5. **Registration:**
     - Stores session in `ProfileRegistry` (thread-safe).
  6. **Return:** Returns the Selenium URL (e.g., `http://host.docker.internal:XXXX`).

- **Stop Profile**: `ProfileOperationService.stop_profile(profile_id, headers)`
  1. **Locking:** Acquires profile lock.
  2. **Check:** If not running (according to Registry), return immediately.
  3. **API Call:** `GET /api/v1/profile/stop/p/{profile_id}`.
  4. **Unregister:** Removes profile from `ProfileRegistry`.

- **Error Handling:**
  - If start fails, attempts an immediate "cleanup" stop command to ensure consistency.

## 5. Proxy Management Flow

- `ProxyManager.generate_proxy()`
  - Selects protocol/session settings.
  - `POST /v1/proxy/connection_url`
  - Returns parsed proxy credentials.

## 6. Infrastructure & Error Handling

- **Base Manager**: `BaseManagerApi`
  - Wraps `HttpClient`.
  - Injects `Authorization: Bearer {token}` headers automatically.
  
- **Exceptions**:
  - `MultiLoginAuthError`: Token or login failures.
  - `MultiLoginServiceError`: Domain-specific failures (e.g., Profile already running, 401 Unauthorized during start).
