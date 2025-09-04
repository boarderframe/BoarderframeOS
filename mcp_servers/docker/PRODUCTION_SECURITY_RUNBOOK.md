# Production Security Runbook
## MCP Server Manager - Enhanced Security Operations

### Table of Contents
1. [Quick Start](#quick-start)
2. [Security Architecture](#security-architecture)
3. [Deployment Procedures](#deployment-procedures)
4. [Security Monitoring](#security-monitoring)
5. [Incident Response](#incident-response)
6. [Backup & Recovery](#backup-recovery)
7. [Compliance & Auditing](#compliance-auditing)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose v2.0+
- 4GB+ RAM
- 20GB+ disk space
- SSL certificates for production use

### Initial Deployment
```bash
# 1. Clone and prepare environment
cd /path/to/mcp-servers/docker
cp .env.production.template .env.production

# 2. Configure secrets (CRITICAL)
# Edit .env.production and replace ALL template values
nano .env.production

# 3. Deploy with security validation
./deploy-production-enhanced.sh

# 4. Verify deployment
./scripts/health-check-enhanced.sh
```

---

## Security Architecture

### Defense in Depth Strategy

#### Layer 1: Network Security
- **Nginx Reverse Proxy**: TLS termination, rate limiting, WAF rules
- **Private Networks**: Isolated container networks
- **Firewall Rules**: Minimal port exposure (80, 443, monitoring)

#### Layer 2: Container Security
- **Non-root Users**: All containers run as non-privileged users
- **Read-only Filesystems**: Immutable container filesystems
- **Resource Limits**: CPU, memory, and PID limits
- **Security Profiles**: AppArmor/SELinux enforcement

#### Layer 3: Application Security
- **Authentication**: JWT-based authentication
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive input sanitization
- **Security Headers**: OWASP-compliant HTTP headers

#### Layer 4: Monitoring & Detection
- **Runtime Security**: Falco for anomaly detection
- **Vulnerability Scanning**: Trivy for image scanning
- **Log Monitoring**: Centralized logging with alerting
- **Performance Monitoring**: Prometheus/Grafana stack

---

## Deployment Procedures

### 1. Pre-deployment Security Checklist

```bash
# Environment validation
./deploy-production-enhanced.sh --dry-run

# Security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image mcp-server-manager:latest

# Configuration validation
docker-compose config --quiet

# SSL certificate verification
openssl x509 -in nginx/ssl/cert.pem -text -noout
```

### 2. Zero-downtime Deployment

```bash
# Rolling update procedure
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  up -d --no-deps --scale mcp-manager=2 mcp-manager

# Health check verification
for i in {1..30}; do
  if curl -f https://localhost/health; then
    echo "Service healthy"
    break
  fi
  sleep 5
done

# Scale down old instances
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  up -d --no-deps --scale mcp-manager=1 mcp-manager
```

### 3. Rollback Procedure

```bash
# Quick rollback to previous image
docker tag mcp-server-manager:latest mcp-server-manager:rollback
docker tag mcp-server-manager:previous mcp-server-manager:latest

# Restart services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  up -d mcp-manager

# Verify rollback
./scripts/health-check-enhanced.sh
```

---

## Security Monitoring

### 1. Real-time Security Dashboard

**Grafana Dashboards:**
- **Security Overview**: `/monitoring/grafana/dashboards/security-overview.json`
- **Runtime Threats**: Falco events and anomalies
- **SSL/TLS Status**: Certificate expiry and configuration
- **Authentication Metrics**: Login attempts and failures

### 2. Automated Security Scanning

```bash
# Continuous vulnerability scanning
docker-compose -f docker-compose.yml -f docker-compose.security.yml \
  up -d security-scanner

# Manual security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/security-reports:/reports \
  mcp-security-scanner:latest
```

### 3. Alert Configuration

**Critical Alerts (PagerDuty):**
- Container escape attempts
- Privilege escalation
- SSL certificate expiry (< 7 days)
- Authentication bypass attempts

**Warning Alerts (Slack):**
- High error rates
- Resource exhaustion
- Suspicious network activity
- Failed security scans

---

## Incident Response

### 1. Security Incident Classification

**P0 - Critical (Immediate Response)**
- Active breach detected
- Data exfiltration in progress
- Service completely unavailable
- Authentication system compromised

**P1 - High (1 hour response)**
- Privilege escalation detected
- SSL certificate expired
- Database access compromised
- DDoS attack in progress

**P2 - Medium (4 hour response)**
- Suspicious activity detected
- Performance degradation
- Failed backups
- Non-critical vulnerabilities

### 2. Incident Response Playbook

#### Step 1: Immediate Assessment
```bash
# Check system status
./scripts/health-check-enhanced.sh

# Review security events
docker-compose logs falco | tail -50

# Check authentication logs
docker-compose logs nginx | grep -E "(401|403)"

# Monitor resource usage
docker stats --no-stream
```

#### Step 2: Containment
```bash
# Block suspicious IPs (if identified)
iptables -A INPUT -s SUSPICIOUS_IP -j DROP

# Rotate compromised credentials
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret=$(openssl rand -hex 32) \
  --dry-run=client -o yaml | kubectl apply -f -

# Scale down affected services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  stop AFFECTED_SERVICE
```

#### Step 3: Investigation
```bash
# Collect logs for analysis
./scripts/collect-incident-logs.sh

# Generate security report
./scripts/security-audit.sh > incident-report-$(date +%Y%m%d_%H%M%S).txt

# Preserve evidence
docker commit CONTAINER_ID evidence-$(date +%Y%m%d_%H%M%S)
```

### 3. Communication Templates

**Security Incident Notification:**
```
SECURITY ALERT: [SEVERITY] - [BRIEF DESCRIPTION]

Incident ID: INC-$(date +%Y%m%d-%H%M%S)
Detected At: $(date)
Affected Systems: [LIST]
Impact Assessment: [DESCRIPTION]
Current Status: [INVESTIGATING/CONTAINED/RESOLVED]

Response Team: [NAMES]
Next Update: [TIME]

Technical Details:
[RELEVANT LOG ENTRIES OR METRICS]
```

---

## Backup & Recovery

### 1. Automated Backup Strategy

**Daily Backups (2 AM UTC):**
```bash
# Redis data
docker-compose exec redis redis-cli SAVE
docker cp mcp-redis:/data/dump.rdb backups/redis-$(date +%Y%m%d).rdb

# Grafana configuration
docker-compose exec grafana tar czf - /var/lib/grafana > \
  backups/grafana-$(date +%Y%m%d).tar.gz

# Application configuration
tar czf backups/config-$(date +%Y%m%d).tar.gz \
  docker-compose*.yml .env.production monitoring/ nginx/
```

**Weekly Security Backups:**
```bash
# Security scan results
tar czf backups/security-$(date +%Y%m%d).tar.gz \
  security-reports/ audit-logs/

# SSL certificates
tar czf backups/ssl-$(date +%Y%m%d).tar.gz nginx/ssl/
```

### 2. Disaster Recovery Procedures

#### RTO: 15 minutes | RPO: 1 hour

**Recovery Steps:**
```bash
# 1. Restore from backup
tar xzf backups/config-YYYYMMDD.tar.gz
docker cp backups/redis-YYYYMMDD.rdb mcp-redis:/data/dump.rdb

# 2. Start core services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml \
  up -d redis mcp-manager

# 3. Verify data integrity
./scripts/data-integrity-check.sh

# 4. Full service restoration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. Security validation
./scripts/post-recovery-security-check.sh
```

---

## Compliance & Auditing

### 1. Security Compliance Framework

**Standards Compliance:**
- **OWASP Top 10**: Application security best practices
- **CIS Docker Benchmark**: Container security hardening
- **NIST Cybersecurity Framework**: Comprehensive security controls
- **ISO 27001**: Information security management

### 2. Audit Logging

**Audit Events Tracked:**
- Authentication attempts (success/failure)
- Authorization decisions
- Configuration changes
- Data access and modifications
- Administrative actions
- Security events and incidents

**Log Retention:**
- Security logs: 7 years
- Application logs: 1 year
- System logs: 90 days
- Backup logs: 3 years

### 3. Regular Security Assessments

**Weekly:**
- Vulnerability scans
- Security patch assessment
- Access review
- Backup verification

**Monthly:**
- Penetration testing (automated)
- Security awareness training
- Incident response drill
- Compliance review

**Quarterly:**
- Full security audit
- Risk assessment update
- Disaster recovery test
- Security policy review

---

## Troubleshooting

### 1. Common Security Issues

#### SSL Certificate Problems
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -noout -dates

# Verify certificate chain
openssl verify -CAfile nginx/ssl/ca.pem nginx/ssl/cert.pem

# Test SSL configuration
openssl s_client -connect localhost:443 -servername localhost
```

#### Authentication Failures
```bash
# Check JWT configuration
docker-compose logs mcp-manager | grep -i jwt

# Verify Redis connectivity
docker-compose exec mcp-manager redis-cli -u $REDIS_URL ping

# Check session store
docker-compose exec redis redis-cli keys "session:*"
```

#### Security Scanner Issues
```bash
# Check scanner status
docker-compose -f docker-compose.security.yml ps security-scanner

# Review scan results
tail -f security-reports/latest-scan.json

# Manual vulnerability scan
trivy image --severity HIGH,CRITICAL mcp-server-manager:latest
```

### 2. Performance Security Issues

#### High Memory Usage
```bash
# Identify memory-intensive containers
docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check for memory leaks
docker-compose logs mcp-manager | grep -i "memory\|heap"

# Monitor garbage collection
docker-compose exec mcp-manager node --expose-gc -e "gc(); console.log(process.memoryUsage())"
```

#### Network Security Issues
```bash
# Monitor network connections
netstat -tupln | grep -E ":80|:443|:8080"

# Check for suspicious traffic
docker-compose logs nginx | grep -v "200\|301\|304"

# Analyze connection patterns
docker-compose exec nginx cat /var/log/nginx/access.log | \
  awk '{print $1}' | sort | uniq -c | sort -nr | head -20
```

### 3. Emergency Procedures

#### Immediate Service Isolation
```bash
# Isolate compromised container
docker network disconnect mcp_network CONTAINER_NAME

# Stop all external access
iptables -A INPUT -p tcp --dport 80 -j DROP
iptables -A INPUT -p tcp --dport 443 -j DROP
```

#### Evidence Preservation
```bash
# Create forensic image
docker commit CONTAINER_ID forensic-evidence-$(date +%Y%m%d_%H%M%S)

# Export container filesystem
docker export CONTAINER_ID > evidence-filesystem-$(date +%Y%m%d_%H%M%S).tar

# Collect all logs
docker-compose logs > incident-logs-$(date +%Y%m%d_%H%M%S).txt
```

---

## Security Contacts

**Emergency Response Team:**
- **Security Lead**: security@company.com
- **DevOps Lead**: devops@company.com  
- **On-call Engineer**: +1-XXX-XXX-XXXX

**External Resources:**
- **Security Vendor**: vendor-support@security-company.com
- **Legal/Compliance**: legal@company.com
- **Insurance Carrier**: claims@cyber-insurance.com

---

*This runbook should be reviewed and updated quarterly or after any significant security incident.*