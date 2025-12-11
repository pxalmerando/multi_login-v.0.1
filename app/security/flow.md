## 1. Password Policy Enforcement

- When a user attempts to register or reset a password, the system invokes `validate_password_strength`.
- The validator checks the plain-text password against strict security rules:
  - **Length**: Must meet `MIN_PASSWORD_LENGTH`.
  - **Complexity**: Must contain uppercase, lowercase, digits, and special characters.
- If any rule is violated, an `HTTPException` (400 Bad Request) is raised immediately with a list of specific errors, preventing weak passwords from entering the system.

## 2. Password Hashing (Storage)

- Once a password passes validation, `AuthSecurity.hash_password` is called.
- The system uses `CryptContext` with the **bcrypt** algorithm to transform the plain text into a secure hash.
- This hash is returned to the service layer to be safely stored in the database.

## 3. Credential Verification (Login)

- During login, the application calls `AuthSecurity.verify_password` with the input password and the stored hash.
- The `passlib` context handles the comparison, returning `True` only if the input matches the hash.

## 4. Access Token Generation (Session)

- Upon successful verification, the system calls `AuthSecurity.create_access_token`.
- **Expiration**: Calculates the `exp` claim based on the current UTC time and the `ACCESS_TOKEN_EXPIRE_MINUTES` configuration.
- **Encoding**: Bundles user data and expiration into a payload.
- **Signing**: Generates a JSON Web Token (JWT) signed with the application's `SECRET_KEY` and specified `ALGORITHM`.
- The encoded token is returned to the client for subsequent authenticated requests.