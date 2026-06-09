# ChargeHero Railway Deployment via Python

Automated deployment script that handles all environment variable setup and deployment.

## Prerequisites

1. **Railway CLI installed:**
   ```bash
   npm install -g @railway/cli
   ```
   Or on macOS:
   ```bash
   brew install railway
   ```

2. **Have these credentials ready:**
   - Twilio Account SID
   - Twilio Auth Token
   - Twilio Phone Number
   - Database URL (from Supabase)

## Quick Start

### Option 1: Interactive Deployment (Recommended for First Time)

```bash
# Navigate to project root
cd D:\Tools\Ticketing tool\ChargeHero

# Run the deployment script
python deploy.py
```

The script will:
1. ✅ Check Railway CLI is installed
2. ✅ Prompt you to login to Railway
3. ✅ Ask for Twilio credentials
4. ✅ Ask for Database URL
5. ✅ Set all 6 environment variables
6. ✅ Trigger deployment
7. ✅ Monitor deployment progress
8. ✅ Test API health endpoint

### Option 2: Manual Railway CLI Commands

If you prefer direct CLI commands:

```bash
# 1. Login to Railway
railway login

# 2. Link to your project (use your project ID)
railway link --id chargehero

# 3. Set environment variables
railway variables set SUPABASE_URL "https://YOUR_PROJECT.supabase.co"
railway variables set SUPABASE_KEY "sb_publishable_XXXXXXXX"
railway variables set SUPABASE_SERVICE_ROLE_KEY "sb_secret_XXXXXXXX"
railway variables set SUPABASE_ANON_KEY "sb_publishable_XXXXXXXX"
railway variables set JWT_SECRET "your_jwt_secret_here"

# 4. Set Twilio credentials (replace with actual values)
railway variables set TWILIO_ACCOUNT_SID "your_account_sid"
railway variables set TWILIO_AUTH_TOKEN "your_auth_token"
railway variables set TWILIO_PHONE_NUMBER "+1234567890"

# 5. Set database URL (from Supabase Connection String)
railway variables set DATABASE_URL "postgresql://user:password@db.PROJECT_ID.supabase.co:5432/postgres"

# 6. View all variables
railway variables

# 7. Deploy
railway deploy

# 8. Watch logs
railway logs --follow
```

### Option 3: Python Script with Custom Values

Create a `.env.deployment` file with your secrets:

```bash
# .env.deployment
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
DATABASE_URL=your_db_url
```

Then run:
```bash
python deploy.py
```

## After Deployment

### Monitor Deployment
```bash
# Watch real-time logs
railway logs --follow

# Check deployment status
railway status

# View environment variables
railway variables
```

### Test the API
```bash
# Get your Railway URL (from dashboard or CLI)
railway url

# Test health endpoint
curl https://chargehero-xxxxx.railway.app/health
```

Expected response:
```json
{
  "status": "ok",
  "environment": "production",
  "version": "1.0.0"
}
```

## Troubleshooting

### Build fails
```bash
# Check build logs
railway logs build

# View deployment status
railway deployments
```

### Environment variables not set
```bash
# List all variables
railway variables

# Update a variable
railway variables set VARIABLE_NAME "new_value"
```

### Healthcheck timeout
Make sure all 6 required environment variables are set:
- SUPABASE_URL
- SUPABASE_KEY
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_ANON_KEY
- JWT_SECRET
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER
- DATABASE_URL

### Database connection issues
Verify DATABASE_URL format:
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

## Environment Variables Reference

| Variable | Required | Source |
|----------|----------|--------|
| SUPABASE_URL | Yes | Supabase Settings |
| SUPABASE_KEY | Yes | Supabase API Keys (publishable) |
| SUPABASE_SERVICE_ROLE_KEY | Yes | Supabase API Keys (secret) |
| SUPABASE_ANON_KEY | Yes | Supabase API Keys (publishable) |
| JWT_SECRET | Yes | Generated (provided) |
| TWILIO_ACCOUNT_SID | Yes | Twilio Console |
| TWILIO_AUTH_TOKEN | Yes | Twilio Console |
| TWILIO_PHONE_NUMBER | Yes | Twilio Console |
| DATABASE_URL | Yes | Supabase Connection String |

## Getting Help

Railway documentation: https://docs.railway.app
Railway CLI reference: https://docs.railway.app/cli/commands

