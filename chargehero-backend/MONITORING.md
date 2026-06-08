# ChargeHero Production Monitoring & Alerts Guide

## Overview

This guide covers setting up comprehensive monitoring, logging, and alerting for production systems to ensure 99.9% uptime and rapid incident response.

## Monitoring Stack

### Recommended Tools

1. **Metrics**: Prometheus/Grafana or DataDog
2. **Logs**: ELK Stack (Elasticsearch, Logstash, Kibana) or Supabase logs
3. **Tracing**: Jaeger or Datadog APM
4. **Uptime**: UptimeRobot or Pingdom
5. **Alerts**: PagerDuty or Opsgenie

### Architecture

```
Application → Metrics/Logs → Monitoring → Alerts → Incident Response
                              ↓
                         Dashboards
```

## Application Instrumentation

### Add Monitoring Dependencies

```bash
pip install prometheus-client opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger
```

### Prometheus Metrics

Create `shared/monitoring.py`:

```python
from prometheus_client import Counter, Histogram, Gauge
from datetime import datetime

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1)
)

# Business metrics
active_engineers = Gauge('active_engineers', 'Number of active engineers')
pending_tickets = Gauge('pending_tickets', 'Number of pending tickets')
dispatched_tickets = Gauge('dispatched_tickets', 'Number of dispatched tickets')
completed_tickets = Counter('completed_tickets_total', 'Total completed tickets')

# SLA metrics
sla_breached = Counter(
    'sla_breached_total',
    'Total SLA breaches',
    ['category']
)

# Error metrics
api_errors = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type']
)
```

### FastAPI Instrumentation

```python
# main.py
from prometheus_client import make_asgi_app
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from shared.monitoring import request_count, request_duration
import time

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middleware for request tracking
class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response

app.add_middleware(MonitoringMiddleware)
```

## Logging Configuration

### Structured Logging

```python
# shared/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id

        return json.dumps(log_data)

def setup_logging(log_level=logging.INFO):
    """Setup structured logging with JSON format."""
    handler = logging.StreamHandler()
    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)

    return logger

# Usage
logger = setup_logging()
logger.info("User logged in", extra={'user_id': user_id})
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational events (logins, actions)
- **WARNING**: Warning messages (high latency, low disk)
- **ERROR**: Error events (failed requests, exceptions)
- **CRITICAL**: Critical events (system down, security breach)

## Key Metrics to Monitor

### API Performance

```yaml
Metrics:
  - Request rate (req/s)
  - Response time (p50, p95, p99)
  - Error rate (errors/total requests)
  - Availability (% of requests successful)

SLOs:
  - Response time p99: <500ms
  - Error rate: <0.1%
  - Availability: >99.9%
```

### Database Performance

```yaml
Metrics:
  - Query latency (ms)
  - Connection pool usage (%)
  - Slow queries (>100ms)
  - Transaction rollbacks

SLOs:
  - Query latency p95: <50ms
  - Connection pool: <80%
  - Slow queries: <1% of total
```

### Business Metrics

```yaml
Metrics:
  - Pending tickets count
  - Average dispatch time (minutes)
  - Engineer availability (%)
  - SLA compliance (%)
  - Customer satisfaction (rating)

Targets:
  - Dispatch time: <15 minutes
  - SLA compliance: >95%
  - Satisfaction: >4.5 stars
  - Engineer utilization: 60-80%
```

### System Health

```yaml
Metrics:
  - CPU usage (%)
  - Memory usage (%)
  - Disk usage (%)
  - Network I/O (MB/s)
  - Container restarts (count)

Thresholds:
  - CPU: Alert >80%
  - Memory: Alert >85%
  - Disk: Alert >90%
  - Restarts: Alert >5/hour
```

## Dashboards

### Real-Time Dashboard

Key panels:
1. **Service Health**
   - Uptime indicator
   - Response time
   - Error rate
   - Traffic (req/s)

2. **SLA Tracking**
   - On-time completion %
   - Average resolution time
   - SLA breaches (count)
   - Breach reasons (chart)

3. **Business Metrics**
   - Active engineers (gauge)
   - Pending tickets (gauge)
   - Jobs in progress (gauge)
   - Customer rating (gauge)

4. **System Resources**
   - CPU usage (%)
   - Memory usage (%)
   - Disk usage (%)
   - Network I/O

### Engineer Dashboard

Panels:
1. **Assignment Status**
   - Available engineers
   - Busy engineers
   - Offline engineers

2. **Performance**
   - Top 10 engineers by jobs completed
   - Average rating by engineer
   - Average resolution time

3. **Dispatch Metrics**
   - Average ETA accuracy
   - Dispatch time distribution
   - Acceptance rate

### Customer Dashboard

Panels:
1. **Ticket Status**
   - Total tickets (all time)
   - Pending tickets
   - In-progress tickets
   - Completed tickets

2. **SLA Tracking**
   - Tickets within SLA
   - Tickets approaching SLA
   - Breached tickets

3. **Satisfaction**
   - Average rating trend
   - Rating distribution
   - Top-rated engineers

## Alert Rules

### Critical Alerts (Page immediately)

```yaml
APIDown:
  condition: up{job="chargehero-api"} == 0
  duration: 1m
  severity: critical
  action: Page on-call engineer

HighErrorRate:
  condition: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
  duration: 5m
  severity: critical
  action: Page on-call engineer

DatabaseDown:
  condition: pg_up == 0
  duration: 1m
  severity: critical
  action: Page on-call DBA

HighCrashRate:
  condition: rate(app_crashes_total[5m]) > 0.1
  duration: 5m
  severity: critical
  action: Page on-call engineer
```

### High Alerts (Escalate within 30min)

```yaml
HighLatency:
  condition: histogram_quantile(0.95, http_request_duration_seconds) > 0.5
  duration: 10m
  severity: high
  action: Alert ops team, investigate

HighMemory:
  condition: memory_usage_percent > 85
  duration: 5m
  severity: high
  action: Alert ops team

HighDiskUsage:
  condition: disk_usage_percent > 85
  duration: 10m
  severity: high
  action: Alert ops team

SLABreach:
  condition: sla_breached_total > 5 (per hour)
  duration: 1h
  severity: high
  action: Alert product team
```

### Medium Alerts (Email notification)

```yaml
SlowQueries:
  condition: rate(db_query_duration_seconds{le="0.1"}[5m]) < 0.9
  duration: 10m
  severity: medium
  action: Email on-call DBA

HighCPU:
  condition: cpu_usage_percent > 75
  duration: 10m
  severity: medium
  action: Email ops team

RateLimitHits:
  condition: rate(rate_limit_exceeded_total[5m]) > 10
  duration: 5m
  severity: medium
  action: Email security team

UnusualTraffic:
  condition: request_rate > baseline * 1.5
  duration: 5m
  severity: medium
  action: Email ops team
```

### Low Alerts (Log only)

```yaml
LowDiskSpace:
  condition: disk_usage_percent > 70
  duration: 1h
  severity: low
  action: Log warning

IncreasedLatency:
  condition: histogram_quantile(0.95, http_request_duration_seconds) > 0.3
  duration: 15m
  severity: low
  action: Log info

DependencyWarning:
  condition: external_api_latency > 2s
  duration: 10m
  severity: low
  action: Log warning
```

## Alert Routing

### Incident Severity Matrix

| Severity | Description | Response Time | Escalation |
|----------|-------------|----------------|------------|
| Critical | Service down or severe data loss | <5min | P1 on-call |
| High | Significant degradation | <30min | P2 on-call + team |
| Medium | Minor issues affecting subset | <2h | Team lead |
| Low | Informational issues | <24h | Log only |

### Escalation Path

```
Alert triggered
    ↓
Slack notification (#alerts)
    ↓
If Critical → PagerDuty (on-call paged)
If High → Email + Slack (team notified)
If Medium → Slack thread (engineering review)
If Low → Logged (no notification)
```

## Incident Response

### On-Call Workflow

1. **Alert Triggered**
   - PagerDuty sends notification
   - Auto-create incident in Slack
   - Page on-call engineer

2. **Acknowledgement**
   - On-call responds within 5 minutes
   - Acknowledge alert in PagerDuty
   - Post in incident channel

3. **Investigation**
   - Check logs for errors
   - Review recent deployments
   - Check metrics and dashboards
   - Communicate status updates

4. **Mitigation**
   - Apply hotfix if possible
   - Rollback if needed
   - Scale resources if needed
   - Document steps taken

5. **Resolution**
   - Verify service healthy
   - Close incident
   - Post-incident review within 24h

### Incident Communication

**Slack Template**:
```
:alert: INCIDENT #<number>
Title: <brief description>
Severity: <Critical/High/Medium/Low>
Status: <Investigating/Mitigating/Resolved>

Current Impact:
- Services affected: <list>
- Users affected: <estimate>
- Started at: <time>

Timeline:
14:30 - Alert triggered
14:32 - On-call acknowledged
14:35 - Identified issue
14:40 - Mitigation applied
14:45 - Service recovered

Next Steps:
- Post-incident review at 15:30
- RCA due by EOD
- Preventive measures TBD
```

## SLA Tracking

### Service Level Objectives

```yaml
API Availability:
  - Target: 99.9%
  - Measurement: Successful requests / total requests
  - Period: Rolling 30 days

Response Time:
  - p99: <500ms
  - p95: <200ms
  - p50: <50ms

Error Rate:
  - Target: <0.1%
  - Excludes: User errors (4xx)

Ticket SLA:
  - Resolution: 2 hours for critical, 24h for others
  - On-time: >95%
```

### Calculating Availability

```python
def calculate_availability(period_days=30):
    """Calculate service availability."""
    total_seconds = period_days * 24 * 60 * 60  # 2,592,000 seconds
    downtime_seconds = get_total_downtime(period_days)
    uptime_seconds = total_seconds - downtime_seconds

    availability_percent = (uptime_seconds / total_seconds) * 100
    return availability_percent

# 99.9% = 43.2 minutes downtime allowed per month
# 99% = 432 minutes downtime allowed per month
```

## Notifications

### Slack Integration

```python
from slack_sdk import WebClient
import os

slack_client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))

def alert_slack(channel: str, message: str, severity: str):
    """Send alert to Slack."""
    color_map = {
        'critical': 'danger',
        'high': 'warning',
        'medium': '#FFA500',
        'low': 'good'
    }

    response = slack_client.chat_postMessage(
        channel=channel,
        attachments=[{
            'color': color_map[severity],
            'title': f'{severity.upper()} Alert',
            'text': message,
            'ts': int(time.time())
        }]
    )

    return response['ok']
```

### Email Alerts

Configure email alerts in:
- Grafana: Alerts → Notification channels
- AlertManager: Alert routing rules
- PagerDuty: Notification rules

## Tools Setup

### Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: production
    team: chargehero

scrape_configs:
  - job_name: 'chargehero-api'
    static_configs:
      - targets: ['api.chargehero.com:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Grafana

1. Add Prometheus data source
2. Import dashboards:
   - Node Exporter Full
   - Prometheus Stats
   - Custom ChargeHero dashboards
3. Setup alert notifications
4. Configure RBAC

### ELK Stack

```yaml
# logstash.conf
input {
  http {
    port => 5000
    codec => json
  }
}

filter {
  date {
    match => ["timestamp", "ISO8601"]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "chargehero-logs-%{+YYYY.MM.dd}"
  }
}
```

## Compliance & Security

### Audit Logging

All actions logged:
- Admin operations with user/timestamp
- API access logs with status codes
- Error traces (without sensitive data)
- Security events (failed logins, rate limits)

### Data Retention

```yaml
Logs:
  - Real-time: 7 days
  - Aggregated: 30 days
  - Archive: 1 year

Metrics:
  - Raw: 15 days
  - Aggregated: 1 year

Backups:
  - Daily: 30 days
  - Weekly: 1 year
```

### Privacy

Never log:
- Passwords or API keys
- PII (unless anonymized)
- Payment information
- Health information

## Maintenance

### Weekly Reviews

- Check for anomalies in metrics
- Review incident trends
- Update alert thresholds
- Verify backup integrity

### Monthly Reviews

- Analyze SLA compliance
- Review system performance
- Plan capacity upgrades
- Update runbooks

### Quarterly Reviews

- Security audit of monitoring
- Dashboard effectiveness review
- Cost analysis
- Disaster recovery test

---

**Last Updated**: 2026-06-09
**Uptime Target**: 99.9%
**RTO (Recovery Time Objective)**: <1 hour
**RPO (Recovery Point Objective)**: <5 minutes
