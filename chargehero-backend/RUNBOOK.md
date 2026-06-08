# ChargeHero Operations Runbook

Quick-reference guide for responding to common production incidents.

## API Service Down

### Detection

- PagerDuty alert: "APIDown"
- Health check endpoint returns non-200
- Error rate > 50%

### Immediate Actions (< 5 minutes)

1. **Confirm issue**
   ```bash
   curl https://api.chargehero.com/health
   railway status  # Check Railway/Render status
   ```

2. **Check recent deployments**
   ```bash
   railway logs | tail -50  # Last 50 log lines
   git log --oneline -5  # Recent commits
   ```

3. **Notify stakeholders**
   - Slack: Post in #incidents channel
   - Status page: Update status.chargehero.com

### Investigation (5-30 minutes)

1. **Check service health**
   ```bash
   railway scale  # Check instance count
   railway logs --tail=100  # Get recent logs
   ```

2. **Check dependencies**
   ```bash
   # Database
   curl https://api.chargehero.com/health | jq .database_health
   
   # External APIs
   curl https://api.chargehero.com/health | jq .external_services
   ```

3. **Review recent changes**
   - Check git diff with previous version
   - Look for configuration changes
   - Review dependency updates

### Resolution

**If recent deployment caused issue:**
```bash
git revert <commit-hash>  # Revert problematic commit
git push origin main
# Railway auto-deploys after push
```

**If database issue:**
```bash
# Check Supabase status
# Restart connection pool (if available)
# Failover to read replica if available
```

**If memory/CPU issue:**
```bash
railway scale instances=2 memory=512
# Increases resources while investigating
```

### Post-Incident

1. Create incident summary
2. Schedule RCA (Root Cause Analysis) for next day
3. Update runbook if new patterns identified

---

## High Error Rate (>1%)

### Detection

- Alert: "HighErrorRate"
- Error rate spike in dashboard
- User complaints in support

### Quick Diagnosis

```bash
# Check error types
curl https://api.chargehero.com/metrics | grep http_requests_total

# Check specific endpoint errors
railway logs | grep ERROR | grep -o 'endpoint=[^ ]*' | sort | uniq -c

# Check for specific error codes
railway logs | grep "500\|502\|503" | head -20
```

### Common Causes & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| 500 Internal Server Error | Application bug | Check logs, rollback if recent deploy |
| 502 Bad Gateway | Service not responding | Restart service, check memory |
| 503 Service Unavailable | Overloaded | Scale up instances |
| 401 Unauthorized | Auth issue | Check JWT secret, verify tokens |
| 404 Not Found | Missing endpoint | Verify client, check API version |

### Emergency Mitigation

```bash
# If 502/503 errors due to overload:
railway scale instances=3 memory=1024

# If 500 errors due to recent deploy:
git revert <bad-commit>
git push origin main

# If database connection errors:
# Increase connection pool size in config
# Or restart Railway service
railway restart
```

---

## High Latency (>500ms p99)

### Detection

- Metric: `request_duration_seconds_bucket{le="0.5"} < 0.99`
- Users reporting slow responses
- Dashboard shows response time spike

### Root Cause Diagnosis

```bash
# Check database queries
railway logs | grep "db_query_duration" | sort -t= -k2 -rn | head -10

# Check slow endpoints
curl https://api.chargehero.com/metrics | grep http_request_duration | sort

# Check external API latency
railway logs | grep "external_api_latency"

# Check resource utilization
railway status  # CPU, memory, disk usage
```

### Fixes by Root Cause

**Slow Database Queries:**
```bash
# Enable query logging in Supabase
# Run EXPLAIN ANALYZE on slow query
# Consider adding index

# Temporary: Enable query caching
# Check CACHE_TTL in config
```

**External API Latency:**
```bash
# Check Anthropic API status (for copilot)
# Increase timeouts temporarily
# Switch to fallback/cached responses
```

**Resource Exhaustion:**
```bash
railway scale instances=2 memory=1024  # Scale up
railway status  # Monitor improvement
```

---

## Database Connection Errors

### Detection

- Errors: "could not connect to server"
- "connection pool exhausted"
- Database operations failing

### Quick Checks

```bash
# Verify Supabase status
curl https://status.supabase.com

# Check connection pool status
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Verify environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY (don't log actual value!)
```

### Fixes

**If Supabase down:**
- Wait for Supabase to recover
- Monitor status.supabase.com
- Notify users of database maintenance

**If connection pool exhausted:**
```bash
# Increase pool size in config
DATABASE_CONNECTION_POOL_SIZE=20

# Kill idle connections
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U postgres \
  -c "SELECT pg_terminate_backend(pg_stat_activity.pid) 
      FROM pg_stat_activity 
      WHERE pg_stat_activity.idle_in_transaction;"

# Restart service to refresh connections
railway restart
```

**If network/firewall issue:**
- Verify IP whitelist in Supabase
- Check VPN/proxy settings
- Verify SSL certificates

---

## Memory Leak / Growing Memory Usage

### Detection

- Alert: "Memory usage > 85%"
- Memory grows over hours/days
- Service becomes unresponsive

### Diagnosis

```bash
# Check memory trend
curl https://api.chargehero.com/metrics | grep memory_usage

# Check for leaks in code
# Review recent code changes
git log --oneline -20 | head -5

# Identify memory consumers
import tracemalloc
tracemalloc.start()
# ... run application ...
tracemalloc.take_snapshot()  # Analyze
```

### Fixes

**Immediate (< 5 min):**
```bash
railway restart  # Restart service
railway scale instances=2  # Increase instances
```

**Short-term (1-2 hours):**
```bash
# Deploy memory profiling code
# Identify and fix memory leaks
# Test locally before deploying
```

**Long-term:**
- Use monitoring to track memory over time
- Add alerts for gradual growth
- Schedule preventive restarts

---

## High CPU Usage (>80%)

### Detection

- Alert: "High CPU usage"
- Service slowness/timeouts
- Increased response latency

### Root Cause Analysis

```bash
# Check CPU trend
curl https://api.chargehero.com/metrics | grep cpu_usage

# Check process list
ps aux | grep python

# Check hot functions (if APM enabled)
# In DataDog/New Relic: Top functions by CPU
```

### Fixes

**Immediate:**
```bash
railway scale instances=2 cpu=2000m  # Scale horizontally/vertically
```

**Investigation:**
1. Check for infinite loops
2. Check for inefficient database queries
3. Check for heavy computations
4. Profile application

---

## Disk Space Low

### Detection

- Alert: "Disk usage > 85%"
- Logs filling disk
- Application failures

### Quick Actions

```bash
# Check disk usage
df -h

# Check large files
du -sh /*

# Check log sizes
du -sh /var/log/*
```

### Fixes

```bash
# Rotate logs
logrotate -f /etc/logrotate.d/chargehero

# Clean old files
find /tmp -mtime +7 -delete

# Increase disk space
# On Railway/Render: upgrade plan or add persistent volume
```

---

## High Rate Limit Hits

### Detection

- Alert: "Rate limit exceeded > 10/min"
- 429 Too Many Requests errors
- Client complaints

### Investigation

```bash
# Check which endpoints
railway logs | grep "rate_limit" | grep -o 'endpoint=[^ ]*' | sort | uniq -c

# Check source IP/user
railway logs | grep "rate_limit" | grep -o 'user_id=[^ ]*' | sort | uniq -c

# Check patterns
railway logs | grep "rate_limit" | tail -20
```

### Fixes

**If legitimate traffic spike:**
```bash
# Increase rate limit temporarily
RATE_LIMIT_API_REQUESTS=200  # Increase from 100

# Or implement smart rate limiting based on user tier
```

**If DDoS attack:**
```bash
# Enable WAF (Web Application Firewall)
# Block suspicious IPs
# Alert security team
# Scale resources if needed
```

**If stuck client:**
```bash
# Contact customer support
# Provide temporary IP whitelist
# Implement exponential backoff for clients
```

---

## Failed Database Backup

### Detection

- Alert: "Backup failed"
- Missing recent backup
- Backup status in Supabase

### Verification

```bash
# Check Supabase backup status
# Log into Supabase dashboard > Settings > Backups

# Verify backup exists
# Check backup date and size

# Test restore (in dev environment)
# Select backup and test restore
```

### Fixes

```bash
# Manual backup
# Log into Supabase
# Click "Backup" in Settings
# Wait for completion

# Verify backup
# Check file size (should be >100MB typically)
# Verify backup date is recent
```

---

## Service Degradation (Slow But Up)

### Detection

- p95 latency > 500ms
- Some requests timing out
- Users report slowness

### Diagnosis

```bash
# Check resource usage
railway status

# Check hot endpoints
curl https://api.chargehero.com/metrics | grep http_request_duration | sort

# Check database
# Monitor slow queries in Supabase dashboard

# Check external services
# Monitor Anthropic API (copilot) latency
```

### Fixes

**Quick wins:**
- Restart service (might be stuck state)
- Clear cache if applicable
- Scale resources

**Investigation:**
- Profile application
- Check database queries
- Monitor external API latency

---

## Customer Reports Issue

### Triage Questions

1. When did issue start?
2. What specific action triggered it?
3. Which customer/engineer account?
4. Error messages seen?
5. Device/app version?

### Investigation Flow

```bash
# Check logs for user
railway logs | grep "user_id=<customer-id>" | tail -50

# Check database
SELECT * FROM auth_users WHERE id = '<customer-id>';
SELECT * FROM jobs_tickets WHERE customer_id = '<customer-id>' ORDER BY created_at DESC;

# Check metrics for that time period
# Use dashboard to find anomalies during issue time

# Test reproduction locally
# If specific flow, try to reproduce with test account
```

### Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| OTP not received | Check Twilio logs, resend OTP |
| Ticket not assigned | Check dispatch algorithm, manually assign |
| Engineer location not updating | Check location tracking, restart app |
| Checklist not submitting | Check network, retry manually |
| Payment failed | Check payment provider, retry |

---

## Incident Communication Template

**For Slack:**
```
:alert: INCIDENT ALERT
Severity: <CRITICAL/HIGH/MEDIUM>
Service: <affected service>
Status: <INVESTIGATING/MITIGATING/RESOLVED>

Issue: <brief description>
Affected Users: <count/percentage>
Started: <time>

Investigation:
- Action 1: Done
- Action 2: In progress
- Action 3: Next

ETA to Resolution: <estimate>
Updates every 15 minutes
```

---

## Escalation Contacts

- **On-Call Engineer**: <phone>
- **Engineering Lead**: <phone>
- **VP Engineering**: <phone>
- **CEO**: <phone>

- **Slack**: #incidents channel
- **PagerDuty**: [link]
- **Status Page**: status.chargehero.com

---

## Preventive Maintenance

### Daily
- Check error rates and dashboards
- Review alerts overnight
- Verify backups completed

### Weekly
- Capacity planning review
- Incident trend analysis
- Dependency update check

### Monthly
- Full system health check
- Performance optimization review
- Security audit

---

**Last Updated**: 2026-06-09
**Last Major Incident**: [date]
**Next Runbook Review**: 2026-09-09
