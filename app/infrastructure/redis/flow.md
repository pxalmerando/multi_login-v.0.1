## 1. System Initialization

- `RedisProfileStorage` initializes the connection to the Redis server.
- `RedisScriptManager` registers essential Lua scripts to ensure atomicity:
  - Loads scripts for `release`, `delete`, `replace`, `add_if_under_limit`, and `acquire_any_available`.
  - Caches the script SHAs to optimize future executions.
- `RedisProfileStatusReporter` prepares to provide real-time monitoring of the pool.

## 2. Acquiring a Profile (Atomic Flow)

- Application calls `acquire_any_available()`.
- `RedisProfileOperations` executes the atomic Lua script:
  - Calculates the `available` profiles by subtracting `in_use` and `deleted` sets from the `pool`.
  - If the list is empty, it returns `nil`.
  - If a profile is found:
    - Selects the first available `profile_id`.
    - Immediately adds it to the `in_use` set to lock it.
    - Returns the locked `profile_id` to the caller.

## 3. Managing Profile Lifecycle

- **Releasing a Profile**:
  - Application calls `release_profile(profile_id)`.
  - The script checks if the profile is currently in `in_use`.
  - If confirmed, it removes the ID from `in_use`, effectively returning it to the available pool.
- **Marking as Deleted**:
  - Application calls `mark_deleted(profile_id)` (e.g., if a profile is banned).
  - The script atomically:
    - Removes the ID from `in_use` (unlocks it).
    - Removes the ID from `pool` (deregisters it).
    - Adds the ID to `deleted` (blacklists it from future addition).

## 4. Pool Monitoring

- Application requests pool status via `get_status()`.
- `RedisProfileStatusReporter` executes a pipeline for efficiency:
  - Counts total profiles in `pool`, `in_use`, and `deleted`.
  - Calculates the specific `available` members.
- Returns a comprehensive status dictionary to the application.