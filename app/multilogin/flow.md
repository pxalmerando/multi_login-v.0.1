# MultiLogin Authentication & Profile Management System - Flow Documentation

## System Overview

This codebase implements a comprehensive authentication and profile management system for the MultiLogin API. The architecture is built on three main layers:

1. **Authentication Layer** - Handles user login, token management, and Redis caching
2. **API Management Layer** - Provides HTTP client wrappers for API interactions
3. **Profile & Workspace Layer** - Manages profiles, folders, and proxies

---


## Authentication Flow

### 1. Token Acquisition Flow

```
Client Code
    │
    └──▶ RedisTokenManager.get_tokens()
         │
         ├──▶ TokenService.get_tokens()
         │   │
         │   ├─ Try load cached tokens from Redis
         │   │
         │   ├─ If cached tokens exist:
         │   │  └─ Validate with TokenValidator
         │   │     └─ Check required fields
         │   │     └─ Check expiration (with 60s grace period)
         │   │
         │   ├─ If valid: Return cached tokens ✓
         │   │
         │   └─ If invalid/expired:
         │      └─ Re-authenticate via UserAuth.login()
         │         │
         │         ├─ Hash password (MD5)
         │         ├─ POST to /user/signin
         │         ├─ Extract access_token, refresh_token
         │         ├─ Calculate expiration (current_time + 30 min)
         │         └─ Return new tokens
         │
         └─ Cache new tokens in Redis (async, non-blocking)
            └─ TokenRepository.save(tokens)
               └─ TokenSerializer.serialize() → JSON string
               └─ Redis SET: auth:tokens = serialized_data
                  (ignores cache errors)
```

### 2. Token Validation Logic

**TokenValidator.is_valid(tokens):**
- Returns `True` only if BOTH conditions pass:
  1. **Structure Check**: `has_required_fields(tokens)`
     - Checks for: `access_token`, `refresh_token`, `token_expiration`
     - Returns `False` if any field is missing or tokens is None/not dict
  
  2. **Expiration Check**: `is_expired(tokens)`
     - Calculates: `effective_expiration = token_expiration + grace_period_seconds` (default 60s)
     - Compares: `now >= effective_expiration`
     - Grace period allows buffer time before actual expiration

### 3. Token Cache Operations

**TokenRepository operations:**

| Operation | Method | Logic |
|-----------|--------|-------|
| **Load** | `load()` | Redis GET → Deserialize JSON → Validate structure |
| **Save** | `save(tokens)` | Serialize to JSON → Redis SET → Handle errors |
| **Delete** | `delete()` | Redis DELETE → Returns bool if successful |
| **Check Exists** | `exists()` | Redis EXISTS → Returns bool |

All Redis operations include comprehensive error handling and logging.

---

## Profile Management Flow

### 1. Profile Creation Flow

```
Client Code
    │
    └──▶ ProfileManager.create_profile(
         folder_id, name, browser_type="mimic", 
         os_type="windows", proxy=None)
         │
         ├─ Build request payload:
         │  ├─ Basic: name, folder_id, browser_type, os_type
         │  └─ Parameters: fingerprint, flags, storage, proxy
         │     ├─ fingerprint: {}
         │     ├─ flags: (13 masking options)
         │     │  ├─ audio_masking, canvas_noise, fonts_masking
         │     │  ├─ geolocation_masking, graphics_masking
         │     │  ├─ media_devices_masking, navigator_masking
         │     │  ├─ ports_masking, proxy_masking, screen_masking
         │     │  └─ timezone_masking, webrtc_masking
         │     └─ storage: {is_local: true, save_service_worker: true}
         │
         └──▶ POST /profile/create (with auth header)
              └─ Response: {data: {id, ...profile_data}}
                 └─ Return full API response
```

### 2. Profile Listing & Retrieval

```
ProfileManager.list_profiles(folder_id, is_removed=False, 
                             limit=100, offset=0, ...)
    │
    └──▶ POST /profile/search (with filters)
         │
         Request payload:
         ├─ folder_id: required
         ├─ is_removed: false (default)
         ├─ limit: 100 (pagination)
         ├─ offset: 0 (pagination)
         ├─ search_text: "" (optional filter)
         ├─ storage_type: "all"
         ├─ order_by: "created_at"
         └─ sort: "asc"
         │
         └──▶ Response: {data: {profiles: [...]}}
              └─ Extract list of profile objects
```

**Helper Methods:**
- `get_profile_ids(folder_id)` → Extract all profile IDs
- `get_profile_names(folder_id)` → Extract all profile names

### 3. Profile Update Flow

```
ProfileManager.update_profile(profile_id, folder_id, name, 
                              browser_type, os_type, proxy)
    │
    ├─ Build payload (same structure as create, but with profile_id)
    │
    └──▶ POST /profile/update (with auth header)
         └─ Response: {data: {...updated_profile}}
```

### 4. Profile Deletion Flow

```
ProfileManager.delete_profile(profile_id, is_permanent=True)
    │
    └──▶ POST /profile/remove
         │
         Payload:
         ├─ ids: [profile_id] (array, even for single)
         └─ permanently: true/false
            - true: hard delete
            - false: soft delete (mark as removed)
         │
         └──▶ Response: {status: "success", ...}
```

---

## Folder Management Flow

### 1. Get or Create Default Folder

```
FolderManager.get_or_create_default_folder(folder_name=None)
    │
    ├─ Check cache (_folder_id_cache)
    │  └─ If cached: Return immediately ✓
    │
    └─ If not cached:
       │
       ├─ GET /workspace/folders
       │  └─ Extract folder_ids from response
       │
       ├─ If folders exist:
       │  ├─ Use first folder ID
       │  ├─ Store in cache
       │  └─ Return ID ✓
       │
       └─ Else (no folders):
          │
          ├─ POST /workspace/folder_create
          │  ├─ name: provided or "Folder {random(1-100)}"
          │  └─ comment: null
          │
          ├─ Extract folder ID from response.data.id
          ├─ Store in cache
          └─ Return ID ✓
```

### 2. Folder Operations

| Operation | Method | Endpoint | Payload |
|-----------|--------|----------|---------|
| **Create** | `create_folder(name, comment)` | `POST /workspace/folder_create` | {name, comment} |
| **List** | `list_folders()` | `GET /workspace/folders` | None |
| **Update** | `update_folder(id, name, comment)` | `POST /workspace/folder_update` | {folder_id, name, comment} |
| **Delete** | `delete_folder(id)` | `POST /workspace/folders_remove` | {ids: [folder_id]} |
| **Get Names** | `get_folder_name()` | Calls list_folders() | - |
| **Get IDs** | `get_folder_ids()` | Calls list_folders() | - |

**Caching Strategy:**
- `_folder_id_cache` stores single folder ID
- `clear_cache()` resets the cache
- Cache prevents repeated API calls for same folder

---

## Proxy Management Flow

### 1. Proxy Generation

```
ProxyManager.generate_proxy()
    │
    ├─ Randomly select:
    │  ├─ Protocol: socks5 or http
    │  └─ Session Type: rotating or sticky
    │
    └──▶ POST /v1/proxy/connection_url
         │
         Payload:
         ├─ country: "any"
         ├─ protocol: (random choice)
         └─ sessionType: (random choice)
         │
         ├─ Response: connection string
         │  Format: "host:port:username:password"
         │
         └──▶ Parse and return:
              {
                "host": extracted,
                "port": extracted,
                "username": extracted,
                "password": extracted
              }
```

### 2. Fetch User Proxy Data

```
ProxyManager.fetch_proxy_data()
    │
    └──▶ GET /v1/user (with auth header)
         └─ Returns: user account/subscription data
```

---

## HTTP Request Flow

### BaseManagerApi Request Pipeline

```
Client Method Call
    │
    ├─ Assemble endpoint path & parameters
    │
    └──▶ request(method, endpoint, include_auth=False, **kwargs)
         │
         ├─ Build headers:
         │  ├─ Content-Type: application/json
         │  ├─ Accept: application/json
         │  └─ Authorization: Bearer {api_token} (if include_auth=True)
         │
         └──▶ HttpClient._make_request(method, endpoint, headers, **kwargs)
              │
              ├─ Construct full URL: {base_url}/{endpoint}
              │
              └──▶ Execute HTTP request
                   ├─ GET, POST, etc.
                   ├─ Attach headers
                   ├─ Send JSON body (if json kwarg)
                   │
                   └─ Return parsed JSON response
```

---

## Error Handling Strategy

### Exception Hierarchy

```
Exception
├─ MultiLoginAuthError
│  └─ Raised by: UserAuth (missing tokens, login failures)
│
└─ MultiLoginServiceError
   └─ Raised by: profile_launch_parser (invalid responses)
```

### Error Recovery

| Layer | Error Type | Handling |
|-------|-----------|----------|
| **Token Service** | Cache load failure | Log warning, proceed with re-auth |
| **Token Service** | Auth failure | Log exception, raise wrapped error |
| **Token Service** | Cache save failure | Log warning, continue (non-blocking) |
| **Token Repository** | Redis error | Log error, raise exception |
| **Token Validator** | Invalid structure | Return False, log warning |
| **Profile Manager** | API error | Log exception, return empty dict |
| **Folder Manager** | API error | Log exception, raise exception |

### Logging Strategy

All components use structured logging with class-specific prefixes:
- `[UserAuth]` - Authentication operations
- `[TokenService]` - Token lifecycle
- `[TokenValidator]` - Validation logic
- `[TokenRepository]` - Redis operations
- `[TokenSerializer]` - Serialization logic
- `[RedisTokenManager]` - High-level token management
- `[ProfileManager]` - Profile operations
- `[FolderManager]` - Folder operations

---

## Data Models

### Token Structure

```python
{
    "access_token": str,
    "refresh_token": str,
    "token_expiration": float  # Unix timestamp
}
```

### MultiLoginProfileSession

```python
{
    "status_code": int,
    "profile_id": str,
    "selenium_port": int,
    "started_at": datetime,
    
    # Computed property:
    "selenium_url": str  # "http://localhost:{selenium_port}"
}
```

### Proxy Configuration

```python
{
    "type": str,          # "http", "socks5", etc.
    "host": str,
    "port": str,
    "username": str,
    "password": str,
    "save_traffic": bool  # optional
}
```

### Profile Parameters

```python
{
    "fingerprint": {},
    "flags": {
        "audio_masking": str,
        "canvas_noise": str,
        "fonts_masking": str,
        "geolocation_masking": str,
        "geolocation_popup": str,
        "graphics_masking": str,
        "graphics_noise": str,
        "localization_masking": str,
        "media_devices_masking": str,
        "navigator_masking": str,
        "ports_masking": str,
        "proxy_masking": str,          # "disabled" or "custom"
        "quic_mode": str,
        "screen_masking": str,
        "startup_behavior": str,
        "timezone_masking": str,
        "webrtc_masking": str
    },
    "storage": {
        "is_local": bool,
        "save_service_worker": bool
    },
    "proxy": {  # optional
        "type": str,
        "host": str,
        "port": str,
        "username": str,
        "password": str
    }
}
```

---

## Key Design Patterns

### 1. **Decorator Pattern**
- `BaseManagerApi` wraps `HttpClient` and adds authentication headers

### 2. **Repository Pattern**
- `TokenRepository` abstracts Redis operations
- Allows easy switching between storage backends

### 3. **Service Pattern**
- `TokenService` orchestrates multiple components
- Separates business logic from infrastructure

### 4. **Caching Strategy**
- Redis-based distributed cache for tokens
- In-memory cache for folder IDs
- Grace period for token expiration (60s buffer)

### 5. **Composition over Inheritance**
- `TokenService` composes: Repository, Validator, UserAuth
- `RedisTokenManager` composes: TokenService

### 6. **Async/Await Pattern**
- All I/O operations are async
- Non-blocking error handling in token caching

---

## Integration Points

### Entry Points for Client Code

```python
# Token Management
redis_token_manager = RedisTokenManager(user_auth, redis_client)
tokens = await redis_token_manager.get_tokens()

# Profile Management
profile_manager = ProfileManager(api_url, api_token)
profile = await profile_manager.create_profile(folder_id, "My Profile")

# Folder Management
folder_manager = FolderManager(api_url, api_token)
folder_id = await folder_manager.get_or_create_default_folder()

# Proxy Management
proxy_manager = ProxyManager(api_url, api_token)
proxy = await proxy_manager.generate_proxy()
```

### Configuration Requirements

1. **Redis Connection**
   - Required for token caching
   - Key format: `auth:tokens` (configurable prefix)

2. **API Credentials**
   - `api_token` for authenticated endpoints
   - Used in Authorization header

3. **User Credentials**
   - `email` and `password` for login
   - Password is MD5 hashed before transmission

4. **API Endpoints**
   - Base URL must be provided
   - Relative endpoints are appended by HTTP client