# ChargeHero Security Configuration Guide

## Environment Variables

All security-sensitive configuration should be stored in environment variables, never hardcoded.

### Required Environment Variables

```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Authentication
JWT_SECRET_KEY=your-secret-key-min-32-characters
OTP_EXPIRY_MINUTES=5
MAX_OTP_ATTEMPTS=3

# AWS S3
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=chargehero-media
S3_PRESIGNED_URL_EXPIRY_MINUTES=10

# Anthropic API
ANTHROPIC_API_KEY=your-api-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
CORS_ALLOW_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_OTP_REQUESTS=5
RATE_LIMIT_OTP_WINDOW_SECONDS=600
RATE_LIMIT_LOGIN_REQUESTS=10
RATE_LIMIT_LOGIN_WINDOW_SECONDS=900
RATE_LIMIT_API_REQUESTS=100
RATE_LIMIT_API_WINDOW_SECONDS=60

# Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true

# Environment
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
```

### Development Environment

For local development, create `.env.development`:

```bash
SUPABASE_URL=http://localhost:54321
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

JWT_SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8081

ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Production Environment

For production, use platform-managed secrets (Railway, Render, etc.):

```bash
# All values should be managed by deployment platform
# Never commit secrets to git
```

## Security Best Practices

### 1. Secret Rotation

- **Frequency**: Rotate critical secrets quarterly
  - JWT_SECRET_KEY
  - AWS credentials
  - Anthropic API key

- **Process**:
  1. Generate new secret
  2. Update in deployment platform
  3. Verify with new secret working
  4. Keep old secret for grace period (24h)
  5. Remove old secret

### 2. Access Control

- **Database Access**:
  - Use `SUPABASE_SERVICE_ROLE_KEY` only in backend
  - Never expose to frontend/mobile apps
  - Use `SUPABASE_KEY` (anon key) for client-side

- **API Keys**:
  - Rotate after employee departure
  - Restrict scopes (e.g., S3 read-only for backups)
  - Monitor usage for anomalies

### 3. Logging Configuration

```python
# In config.py
import logging

logging.basicConfig(
    level=logging.getLevelName(os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chargehero.log'),
        logging.StreamHandler()
    ]
)

# Never log sensitive data
# ❌ logger.info(f"User {user_id} logged in with password: {password}")
# ✅ logger.info(f"User {user_id} logged in successfully")
```

### 4. Database Security

#### Row-Level Security (RLS)

All public tables must have RLS enabled:

```sql
-- Enable RLS on tables
ALTER TABLE auth_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs_service_reports ENABLE ROW LEVEL SECURITY;

-- Create policies for customers (see own tickets)
CREATE POLICY "Customers see own tickets"
ON jobs_tickets FOR SELECT
USING (customer_id = auth.uid());

-- Create policies for engineers (see assigned tickets)
CREATE POLICY "Engineers see assigned tickets"
ON jobs_tickets FOR SELECT
USING (assigned_engineer_id = auth.uid());

-- Create policies for admins (see all)
CREATE POLICY "Admins see all tickets"
ON jobs_tickets FOR ALL
USING (is_admin() = true);
```

#### Connection String

Never put credentials in connection strings:

```python
# ❌ Bad
url = f"postgresql://{user}:{password}@{host}/{db}"

# ✅ Good
url = os.getenv('DATABASE_URL')
```

### 5. CORS Configuration

Configure CORS strictly for production:

```python
from fastapi.middleware.cors import CORSMiddleware

# Production configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
    allow_headers=['Authorization', 'Content-Type'],
)
```

### 6. Input Validation

Use Pydantic for automatic validation:

```python
from pydantic import BaseModel, Field, validator
from shared.security import InputValidator

class UserRegistrationRequest(BaseModel):
    phone: str
    email: str
    name: str

    @validator('phone')
    def validate_phone(cls, v):
        if not InputValidator.validate_phone(v):
            raise ValueError('Invalid phone number')
        return v

    @validator('email')
    def validate_email(cls, v):
        if not InputValidator.validate_email(v):
            raise ValueError('Invalid email')
        return v

    @validator('name')
    def validate_name(cls, v):
        if not InputValidator.validate_no_xss(v):
            raise ValueError('Invalid characters in name')
        return v.strip()
```

### 7. Rate Limiting

Apply rate limiting to sensitive endpoints:

```python
from shared.security import rate_limit

@router.post("/auth/register")
@rate_limit(max_attempts=5, window_seconds=3600)
async def register(request: RegistrationRequest):
    # Registration limited to 5 per hour
    pass

@router.post("/auth/login/otp")
@rate_limit(max_attempts=10, window_seconds=900)
async def send_login_otp(request: LoginOTPRequest):
    # Login OTP limited to 10 per 15 minutes
    pass
```

### 8. Error Handling

Never expose sensitive information in error responses:

```python
from shared.error_handler import ChargeHeroException, ErrorHandler

try:
    user = db.get_user(user_id)
except Exception as e:
    # ❌ Bad: exposes internal error
    # return {'error': str(e)}

    # ✅ Good: generic error to client, details logged
    logger.error(f"Error fetching user {user_id}: {e}")
    raise HTTPException(
        status_code=500,
        detail="Failed to fetch user details"
    )
```

### 9. Audit Logging

Log all sensitive operations:

```python
from shared.security import AuditLogger, get_client_ip

@router.patch("/admin/engineers/{engineer_id}")
async def update_engineer(
    engineer_id: str,
    request: EngineerUpdateRequest,
    current_user = Depends(get_current_user),
    request_obj = Depends(get_request)
):
    # Perform update...

    # Log the action
    AuditLogger.log_admin_action(
        admin_id=current_user['id'],
        action='update_engineer',
        resource_id=engineer_id,
        changes=request.model_dump(),
        ip_address=get_client_ip(request_obj)
    )
```

### 10. Password Security

Use bcrypt for password hashing:

```python
from shared.security import PasswordSecurity

# Hash password during registration
hashed_password = PasswordSecurity.hash_password(user_password)

# Verify during login
is_valid = PasswordSecurity.verify_password(provided_password, hashed_password)

# Validate password strength
is_strong, error_msg = PasswordSecurity.validate_password_strength(password)
if not is_strong:
    raise ValueError(error_msg)
```

## Deployment Checklist

Before deploying to production, verify:

- [ ] All environment variables configured securely
- [ ] Database RLS policies enabled on all tables
- [ ] CORS origins restricted to production domain only
- [ ] HTTPS enforced (no HTTP)
- [ ] Security headers verified
- [ ] Rate limiting enabled on all public endpoints
- [ ] Audit logging enabled
- [ ] Error messages don't expose sensitive data
- [ ] API keys rotated since last deployment
- [ ] Secrets stored in platform secret manager (not code)
- [ ] Log rotation configured (max 30 days)
- [ ] Backup encryption enabled
- [ ] Database backup tested
- [ ] Incident response contacts documented
- [ ] Security contacts (security@chargehero.com) active

## Monitoring & Alerts

### Suspicious Activity Alerts

Configure alerts for:

1. **Multiple Failed Logins**
   - 5+ failed attempts in 15 minutes → lock account
   - Alert admin

2. **Rate Limit Violations**
   - Repeated API rate limit hits → log suspicious activity
   - Potential DDoS indicator

3. **Unusual Admin Actions**
   - Multiple engineer status changes
   - Bulk user modifications
   - High-frequency operations

4. **Security Errors**
   - Validation failures
   - Authorization denials
   - Encryption failures

### Logging Review

Review logs daily for:

- `AUTH_ATTEMPT` failures
- `ADMIN_AUDIT` changes
- `SECURITY_EVENT` warnings

```bash
# Check for failed login attempts
grep "AUTH_ATTEMPT.*success.*false" logs/chargehero.log | wc -l

# Check for security events
grep "SECURITY_EVENT.*severity.*HIGH" logs/chargehero.log

# Check for admin actions
grep "ADMIN_AUDIT" logs/chargehero.log
```

## Incident Response

### Security Incident Response Process

1. **Detection**: Automated alerts and manual logs review
2. **Containment**: Disable affected accounts, isolate services
3. **Investigation**: Review logs, identify root cause
4. **Remediation**: Fix vulnerability, patch system
5. **Recovery**: Restore services, verify functionality
6. **Post-Incident**: Document lessons learned, update procedures

### Reporting Process

- **Internal**: Report to security team within 1 hour
- **External**: 72-hour disclosure for non-critical vulnerabilities
- **Users**: Notify affected users within 24 hours if data exposed
- **Regulators**: Follow compliance requirements (if applicable)

## Contacts

- **Security Team**: security@chargehero.com
- **Incident Response**: oncall-security@chargehero.com
- **General Support**: support@chargehero.com

---

**Last Updated**: 2026-06-09
**Next Review**: 2026-09-09
