# MultiLogin Auth, Profile, Folder & Proxy – Flow Overview

## 1. Authentication & Token Flow

- Client calls `RedisTokenManager.get_tokens()`
  - `TokenService` tries to load tokens from Redis via `TokenRepository`
    - `TokenValidator` checks:
      - required fields present
      - not expired (60s grace)
  - If valid:
    - return cached tokens ✓
  - Else:
    - `UserAuth.login()`:
      - MD5‑hash password
      - `POST /user/signin`
      - extract `access_token`, `refresh_token`
      - compute `token_expiration`
    - `TokenRepository` saves tokens to Redis
      - cache failures are logged, non‑fatal

## 2. Profile Management Flow

- `ProfileManager.create_profile(...)`
  - build payload:
    - name, folder_id, browser/OS
    - fingerprint, flags, storage, optional proxy
  - `POST /profile/create`
  - return full API response

- `ProfileManager.list_profiles(...)`
  - `POST /profile/search`
  - filters: folder_id, is_removed, search_text
  - pagination: limit, offset
  - returns profiles list

- `ProfileManager.update_profile(...)`
  - `POST /profile/update`
  - returns updated profile

- `ProfileManager.delete_profile(profile_id, is_permanent)`
  - `POST /profile/remove`
  - payload: `{ ids: [profile_id], permanently: bool }`

## 3. Folder Management Flow

- `FolderManager.get_or_create_default_folder(...)`
  - check in‑memory `_folder_id_cache`
    - if present: return ID ✓
  - if not cached:
    - `GET /workspace/folders`
      - if any folders:
        - use first folder ID
        - cache + return ✓
      - else:
        - `POST /workspace/folder_create`
        - extract new folder ID
        - cache ID
        - return ID ✓

- Other folder operations
  - `create_folder` → `POST /workspace/folder_create`
  - `list_folders` → `GET /workspace/folders`
  - `update_folder` → `POST /workspace/folder_update`
  - `delete_folder` → `POST /workspace/folders_remove`

## 4. Proxy Management Flow

- `ProxyManager.generate_proxy()`
  - randomly pick:
    - protocol: `http` or `socks5`
    - sessionType: `rotating` or `sticky`
  - `POST /v1/proxy/connection_url`
    - payload: `{ country, protocol, sessionType }`
    - response: `"host:port:username:password"`
    - parse to proxy dict `{host, port, username, password}`

- `ProxyManager.fetch_proxy_data()`
  - `GET /v1/user`
  - returns account/subscription data

## 5. HTTP & Error Handling

- `BaseManagerApi.request(method, endpoint, include_auth, **kwargs)`
  - build URL: `{base_url}/{endpoint}`
  - build headers:
    - `Content-Type: application/json`
    - `Accept: application/json`
    - `Authorization: Bearer {api_token}` (if `include_auth=True`)
  - call `HttpClient._make_request(...)`
    - execute GET/POST with JSON
    - return parsed JSON

- Errors
  - `MultiLoginAuthError` → login/token failures
  - `MultiLoginServiceError` → invalid service responses
  - Redis/API errors are logged; token cache writes are non‑blocking