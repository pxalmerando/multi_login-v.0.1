# Auth Feature – Flow Overview

## Files

- api/routes.py  
  - FastAPI endpoints: /auth/register, /auth/login
- services/user_service.py  
  - UserService: creates users with validation
- services/auth_service.py  
  - AuthService: authenticates users and builds AuthToken responses
- repository.py  
  - UserRepository: in-memory user storage (get/create/email_exist)
- schemas.py  
  - UserCreate, UserInDB, UserBase, AuthToken
- security (app/security)  
  - AuthSecurity: hash/verify passwords, create JWT tokens  
  - validate_password_strength: enforce password rules

---

## Register Flow (/auth/register)

1. Client sends `POST /auth/register` with `UserCreate` body  
   - email, password, optional username/first/last name.
2. `register_user` (api/routes.py)  
   - Calls `user_service.create_user(user_data)`.
3. `UserService.create_user`  
   - Validates password strength with `validate_password_strength`.  
   - Checks `UserRepository.email_exist(email)`; if yes → raises `EmailAlreadyRegisteredError`.  
   - Hashes password via `AuthSecurity.hash_password`.  
   - Builds `UserInDB` and saves via `UserRepository.create_user`.  
   - Returns the stored `UserInDB`.
4. Route calls `AuthService.create_auth_response(user_in_db)`  
   - Uses `AuthSecurity.create_access_token` with user email as `sub`.  
   - Maps `UserInDB` → `UserBase` (no password).  
   - Returns `AuthToken` (access_token, token_type, user).
5. Client receives `AuthToken` and can use `access_token` for authenticated requests.

---

## Login Flow (/auth/login)

1. Client sends `POST /auth/login` using `OAuth2PasswordRequestForm`  
   - username (email) and password.
2. `login_user` (api/routes.py)  
   - Calls `AuthService.authenticate_user(email, password)`.
3. `AuthService.authenticate_user`  
   - Fetches user via `UserRepository.get_user_by_email(email)`.  
   - If not found or password invalid (`AuthSecurity.verify_password`) → returns None (or raises InvalidCredentialsError if you refactor).  
   - On success → returns `UserInDB`.
4. Route behavior  
   - If no user: raises HTTP 401 with `ERROR_INVALID_CREDENTIALS`.  
   - If user: calls `AuthService.create_auth_response(user)` and returns `AuthToken`.
5. Client receives `AuthToken` and uses `access_token` for future requests.

---

## Key Decisions

- Password rules are centralized in `app/security/password_policy.py`.  
- Hashing and JWT logic are in `app/security/hashing.py` (`AuthSecurity`).  
- Auth routes are thin; they delegate to services and rely on schemas for data shapes.