# ChargeHero Backend Deployment Guide

## Overview

This guide covers deploying the ChargeHero backend to Railway or Render with production-grade configuration.

## Prerequisites

- Docker installed locally
- Railway or Render account
- GitHub repository access
- Environment variables configured securely
- Supabase project created and configured

## Environment Setup

### Development Environment

1. Clone repository:
```bash
git clone https://github.com/yourorg/chargehero.git
cd chargehero/chargehero-backend
```

2. Create `.env.development`:
```bash
cp .env.example .env.development
# Edit with local Supabase URL and keys
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

4. Run locally:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Staging Environment

1. Create Railway/Render project for staging
2. Set environment variables in platform UI or via CLI
3. Connect GitHub repository
4. Configure branch to `develop`

### Production Environment

1. Create separate Railway/Render project for production
2. Set environment variables securely
3. Connect GitHub repository
4. Configure branch to `main` with version tags only

## Deployment Methods

### Method 1: Railway (Recommended)

#### Initial Setup

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login to Railway:
```bash
railway login
```

3. Create new project:
```bash
railway init
```

4. Add environment variables:
```bash
railway variables set SUPABASE_URL=https://...
railway variables set JWT_SECRET_KEY=your-secret-key
railway variables set ENVIRONMENT=production
# ... set all required variables
```

5. Deploy:
```bash
railway up
```

#### GitHub Integration

1. Link repository to Railway project
2. Set deployment branch (main for production, develop for staging)
3. Enable automatic deployments on push
4. Configure health check: `/health` endpoint

#### Monitoring

1. View logs:
```bash
railway logs
```

2. Monitor metrics:
```bash
railway status
```

3. Scale application:
```bash
railway scale instances=2 memory=512
```

### Method 2: Render

#### Initial Setup

1. Connect GitHub repository on render.com
2. Create new Web Service:
   - Name: `chargehero-api`
   - Region: `Singapore` (or closest to users)
   - Runtime: `Docker`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`

3. Set environment variables in Render dashboard

4. Deploy automatically from GitHub on push

#### Configuration

```yaml
# render.yaml (in project root)
services:
  - type: web
    name: chargehero-api
    runtime: docker
    region: singapore
    healthCheckPath: /health
    healthCheckTimeout: 10
    env:
      - key: ENVIRONMENT
        value: production
      - key: LOG_LEVEL
        value: INFO
    autoDeploy: true
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: JWT_SECRET_KEY
        sync: false
```

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All tests passing locally
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Secrets stored securely (not in code)
- [ ] CORS origins configured for production domain
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Security headers verified
- [ ] Health check endpoint working
- [ ] Database backups tested
- [ ] Monitoring configured
- [ ] Alert contacts updated
- [ ] Incident response plan reviewed

## Deployment Steps

### Staging Deployment

1. Push to `develop` branch:
```bash
git checkout develop
git pull
# Make changes...
git push origin develop
```

2. GitHub Actions automatically runs tests and deploys to staging

3. Verify staging deployment:
```bash
curl https://staging-api.chargehero.com/health
```

### Production Deployment

1. Create release branch:
```bash
git checkout main
git pull origin main
```

2. Tag release:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

3. GitHub Actions automatically deploys to production

4. Verify production deployment:
```bash
curl https://api.chargehero.com/health
```

## Post-Deployment Verification

### Health Checks

```bash
# Check API health
curl https://api.chargehero.com/health

# Check database connectivity
curl https://api.chargehero.com/health | jq .

# Verify API response
curl -H "Authorization: Bearer test-token" \
  https://api.chargehero.com/admin/dashboard
```

### Smoke Tests

```bash
# Test registration endpoint
curl -X POST https://api.chargehero.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "email": "test@example.com", "name": "Test"}'

# Test job creation
curl -X POST https://api.chargehero.com/api/v1/jobs/tickets \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"charger_id": "123", "issue_category": "charging_failure"}'
```

## Rollback Procedure

If deployment has critical issues:

### Automatic Rollback (within 5 minutes)

The deployment pipeline supports automatic rollback:

1. Identify failing deployment
2. Revert to previous version:
```bash
railway rollback
# or
render-cli rollback --service chargehero-api --to-version <version-id>
```

### Manual Rollback

1. Deploy previous version:
```bash
git checkout main
git reset --hard <previous-commit>
git push --force-with-lease origin main
```

2. Verify rollback worked:
```bash
curl https://api.chargehero.com/health
```

3. Notify team of rollback
4. Investigate root cause
5. Plan fix for next deployment

## Monitoring & Logs

### View Logs

#### Railway:
```bash
railway logs --tail
```

#### Render:
```bash
# Via Render dashboard > Logs tab
# Or via API:
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/<service-id>/events
```

### Common Issues

#### Out of Memory
- Increase memory allocation in platform
- Optimize database queries
- Enable caching

#### Slow Responses
- Check database performance
- Monitor API response times
- Review slow query logs

#### Database Connection Errors
- Verify Supabase connection string
- Check Supabase service role key
- Verify network connectivity

#### High CPU Usage
- Profile application code
- Reduce concurrent request handling
- Optimize algorithms

## Maintenance

### Database Backups

Supabase automatic backups:
- Daily backups retained for 30 days
- Manual backups available via UI
- Restore from backup if needed

Verify backups:
```bash
# Check backup status in Supabase dashboard
# Settings > Backups
```

### Dependency Updates

Monthly process:
1. Check for security updates
2. Test updates locally
3. Deploy to staging first
4. Verify with smoke tests
5. Deploy to production

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Test thoroughly before deploying
pytest tests/
```

### Health Monitoring

Set up monitoring for:
- API response time (target: <200ms p95)
- Error rate (target: <0.1%)
- Database query time (target: <100ms)
- Memory usage (target: <80%)
- Uptime (target: >99.9%)

## Scaling

### Horizontal Scaling (Multiple Instances)

Railway:
```bash
railway scale instances=2 memory=512
```

Render: Configure via dashboard
- Plans: Free, Starter, Standard, Pro
- Auto-scaling not available (manual scaling)

### Vertical Scaling (More Resources)

- Increase memory allocation
- Use more powerful CPU instance
- Upgrade to paid tier

### Database Scaling

Supabase:
- Upgrade project tier if hitting limits
- Enable replication for read scaling
- Optimize queries and indexes

## Disaster Recovery

### Data Loss Recovery

1. Restore from Supabase backup:
   - Go to Supabase dashboard
   - Settings > Backups
   - Select backup date
   - Click "Restore"

2. Verify data integrity:
```bash
curl https://api.chargehero.com/admin/dashboard
```

### Service Unavailability Recovery

1. Check status page and logs
2. Identify root cause
3. Apply fix or rollback
4. Verify service health
5. Notify users of restoration

### Incident Response

- On-call team contacts: [list]
- Escalation path: [define]
- Communication channel: Slack #incidents
- Post-incident review within 24 hours

## Security in Production

- All traffic over HTTPS only
- API keys rotated quarterly
- Database credentials in secure vaults
- Audit logs enabled and monitored
- Rate limiting active on all endpoints
- Web Application Firewall (WAF) enabled

## Cost Optimization

### Reducing Costs

1. Right-size instance (don't overprovision)
2. Use caching to reduce database queries
3. Optimize asset sizes
4. Monitor bandwidth usage
5. Clean up unused services

### Cost Monitoring

Railway/Render dashboard shows:
- Compute usage
- Data transfer
- Storage usage
- Projected monthly cost

Set budget alerts to avoid surprises.

## Support & Documentation

- **Deployment Issues**: [deployment-support@chargehero.com]
- **Security Issues**: [security@chargehero.com]
- **General Support**: [support@chargehero.com]
- **Status Page**: https://status.chargehero.com

---

**Last Updated**: 2026-06-09
**Next Review**: 2026-09-09
