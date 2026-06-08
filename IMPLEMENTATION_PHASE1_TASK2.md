# Phase 1, Task 2: Auth Domain Implementation - COMPLETED

## Overview
Successfully implemented the authentication domain with registration flow, OTP verification, and JWT token management. All 39 unit tests passing.

## Files Created

### Core Auth Domain (chargehero-backend/domains/auth/)

1. **__init__.py** - Package marker
   - Package initialization for auth domain

2. **models.py** - Pydantic validation schemas
   - `UserRole` enum: engineer, customer, admin
   - `RegistrationStatus` enum: phone_verified → training_completed progression
   - `RegisterRequest`: phone (+919876543210), email, name, dob with validation
   - `VerifyOTPRequest`: phone, 6-digit OTP validation
   - `LoginRequest` / `LoginOTPRequest`: phone/OTP for login flow
   - `SubmitBasicInfoRequest`: bank_account, ifsc_code, upi_id validation
   - Response models: `RegistrationResponse`, `TokenResponse`, `UserResponse`

3. **service.py** - Business logic layer
   - `AuthService` class handling:
     - OTP generation: 6-digit random strings
     - OTP verification: 5-minute expiry, 3-attempt limit
     - Registration creation/retrieval/updates via Supabase
     - JWT token creation with sub, role, iat, exp claims
     - JWT token verification with expiry checking
   - In-memory OTP store (production: use Redis)

4. **routes.py** - FastAPI endpoints
   - `POST /api/v1/auth/register` → Send OTP for new registration
   - `POST /api/v1/auth/register/verify-otp` → Verify OTP, mark phone_verified
   - `POST /api/v1/auth/login` → Send OTP for login
   - `POST /api/v1/auth/login/verify-otp` → Verify login OTP, return JWT token
   - `GET /api/v1/auth/health` → Health check endpoint
   - Full error handling: 409 duplicates, 401 invalid OTP, 404 not found, 503 DB errors

5. **dependencies.py** - Dependency injection
   - `get_current_user(token)` → Extract user from JWT bearer token
   - `get_admin_user(current_user)` → Admin authorization gate
   - `get_engineer_user(current_user)` → Engineer authorization gate
   - HTTPBearer security scheme integration

6. **tests.py** - Comprehensive test suite (39 tests)

### Test Infrastructure

7. **conftest.py** - Pytest configuration
   - Environment setup from .env.test before imports
   - Mock fixtures for Supabase/psycopg2 (not required for testing)
   - Mock database instances with chainable mocks

8. **.env.test** - Test environment variables
   - All required settings for testing without secrets

### Modified Files

9. **main.py** - FastAPI app setup
   - Added: `from domains.auth.routes import router as auth_router`
   - Added: `app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])`

10. **requirements.txt**
    - Updated: PyJWT==2.13.0 (was 2.8.1, unavailable)
    - Added: email-validator==2.1.0

## Test Coverage (39 tests)

### OTP Tests (9 tests)
- Generation: length=6, digits only, uniqueness
- Verification: valid OTP, invalid OTP, nonexistent phone, expiry (5min), max attempts (3), cleanup

### JWT Tests (8 tests)
- Token creation and decoding
- Verification with valid/invalid/expired tokens
- Claims validation: sub, role, exp, iat all present

### Model Validation Tests (22 tests)
- RegisterRequest: phone format/length/digits, email, age (18+)
- VerifyOTPRequest: OTP length/digits
- LoginRequest: phone format
- SubmitBasicInfoRequest: bank account, IFSC code, UPI ID patterns
- Edge cases: exactly 18 years old, various UPI formats

All tests use mocked database to avoid external dependencies.

## Key Features

### Phone Validation
- Format: +91 prefix + 10 digits = 13 chars total
- Rejects: 9876543210 (missing +91), +91987654321 (12 chars), non-digits

### Email Validation
- Uses Pydantic's EmailStr for standard email validation
- Rejects: "not-an-email", invalid formats

### Age Validation
- Requires 18+ years (DOB calculation)
- Rejects: users under 18
- Accepts: exactly 18 years old

### OTP Behavior
- 6-digit generation: random.choices(digits, k=6)
- Expiry: 5 minutes from generation
- Attempt limit: 3 wrong attempts before invalidation
- Cleanup: automatic removal on valid verification or expiry

### JWT Token
- Algorithm: HS256 (configurable via JWT_ALGORITHM)
- Expiry: 24 hours (configurable via JWT_EXPIRY_HOURS)
- Claims: sub (user_id), role, iat (issued at), exp (expiration)
- Signature: HMAC with JWT_SECRET from config

### Banking Information
- Bank account: 9-18 digits
- IFSC code: exactly 11 characters
- UPI ID: pattern [a-zA-Z0-9._-]+@[a-zA-Z]+ (e.g., user@bank, john_doe@icici)

## Architecture Notes

### Separation of Concerns
- Models: Request/response validation only
- Service: Business logic, OTP/JWT operations, DB calls
- Routes: HTTP request/response handling
- Dependencies: Token verification and authorization

### Database Integration
- Uses Supabase client through shared.database.SupabaseDB
- Lazy initialization via get_db_instance()
- Service methods: create_registration, get_registration, update_registration
- Raw table operations: .table().select().eq().execute() pattern

### Error Handling
- Validation: Pydantic raises ValidationError automatically
- HTTP: FastAPI HTTPException with status codes
- Logging: All operations logged (OTP send, token creation, DB errors)

### Security
- No secrets in code or logs
- OTP expires automatically
- JWT verification on every protected request
- Role-based access control via dependencies
- Password hashing TODO (for next phase)

## Testing Approach

### No External Dependencies
- Database mocked entirely
- OTP store in-memory for testing
- No Twilio SMS actually sent (logged instead)
- All tests run in <1 second

### Fixtures Used
- `mock_db`: Mocked Supabase client
- `auth_service`: AuthService with mock DB
- Environment setup via conftest.py

### Test Organization
- Classes by feature: OTPGeneration, OTPVerification, JWTToken, etc.
- Descriptive test names: test_verify_otp_expired, test_invalid_phone_format
- Separate integration tests for DB operations

## Next Steps (Phase 1, Task 3+)

1. Implement KYC verification domain
2. Add training assignment and completion tracking
3. Create password management (for customer support logins)
4. Add email verification (optional 2FA)
5. Implement rate limiting on OTP endpoints
6. Move OTP store from memory to Redis
7. Integrate real Twilio SMS sending (requires credentials)
8. Add audit logging for authentication events

## Verification

```bash
cd chargehero-backend
python -m pytest domains/auth/tests.py -v
# Result: 39 passed in 0.66s
```

## API Endpoints Ready

```
POST   /api/v1/auth/register                    - Start registration
POST   /api/v1/auth/register/verify-otp        - Verify registration OTP
POST   /api/v1/auth/login                       - Start login
POST   /api/v1/auth/login/verify-otp           - Login OTP verification + JWT
GET    /api/v1/auth/health                      - Health check

Protected endpoints use: Authorization: Bearer <JWT_TOKEN>
```

## Configuration Required

From chargehero-backend/.env:
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- JWT_SECRET (minimum 32 chars recommended)
- JWT_ALGORITHM (default: HS256)
- JWT_EXPIRY_HOURS (default: 24)
- TWILIO_ACCOUNT_SID (for SMS, optional for dev)
- TWILIO_AUTH_TOKEN (for SMS, optional for dev)
- TWILIO_PHONE_NUMBER (for SMS, optional for dev)

