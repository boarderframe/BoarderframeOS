# Security Implementation Guide & Test Cases

## Quick Start Security Fixes

### 1. Environment Variables Setup
Create a `.env` file for production (never commit to git):

```bash
# .env.production
REDIS_PASSWORD=$(openssl rand -base64 32)
WEBUI_SECRET_KEY=$(openssl rand -base64 64)
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)
SESSION_SECRET=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
```

### 2. Generate TLS Certificates

```bash
# For development/testing (self-signed)
mkdir -p docker/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/key.pem \
  -out docker/nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# For production (Let's Encrypt)
docker run -it --rm \
  -v $(pwd)/docker/nginx/ssl:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d your-domain.com \
  --agree-tos \
  --email your-email@example.com
```

### 3. Create HTTP Basic Auth File

```bash
# Install htpasswd if not available
apt-get install apache2-utils # Debian/Ubuntu
yum install httpd-tools        # RHEL/CentOS

# Create password file
htpasswd -c docker/nginx/.htpasswd admin
# Add additional users
htpasswd docker/nginx/.htpasswd monitoring_user
```

### 4. Update Docker Compose for Security

```bash
# Use the secure configuration
cp docker/nginx/nginx-secure.conf docker/nginx/nginx.conf

# Start with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Security Test Cases

### Test 1: Authentication & Authorization

```bash
# Test 1.1: Verify authentication is required
echo "Testing unauthenticated access..."
curl -I http://localhost/api/servers
# Expected: 401 Unauthorized

# Test 1.2: Test with valid credentials
echo "Testing authenticated access..."
curl -H "Authorization: Bearer $TOKEN" http://localhost/api/servers
# Expected: 200 OK

# Test 1.3: Test rate limiting on login
echo "Testing login rate limiting..."
for i in {1..10}; do
  curl -X POST http://localhost/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"wrong"}'
done
# Expected: 429 Too Many Requests after 3 attempts
```

### Test 2: Security Headers Validation

```bash
# Test all security headers
echo "Testing security headers..."
curl -I https://localhost/ -k | grep -E "X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security|Content-Security-Policy"

# Validate CSP
echo "Testing CSP..."
curl -I https://localhost/ -k | grep "Content-Security-Policy"
# Should NOT contain 'unsafe-inline' or 'unsafe-eval'
```

### Test 3: Input Validation & Injection Prevention

```bash
# Test 3.1: SQL injection attempt
echo "Testing SQL injection prevention..."
curl -X POST https://localhost/api/search -k \
  -H "Content-Type: application/json" \
  -d '{"query":"test\" OR \"1\"=\"1"}'
# Expected: Properly escaped or rejected

# Test 3.2: XSS attempt
echo "Testing XSS prevention..."
curl -X POST https://localhost/api/comment -k \
  -H "Content-Type: application/json" \
  -d '{"text":"<script>alert(\"XSS\")</script>"}'
# Expected: Content properly escaped in response

# Test 3.3: Path traversal attempt
echo "Testing path traversal prevention..."
curl https://localhost/api/file?path=../../../etc/passwd -k
# Expected: 403 Forbidden or 404 Not Found
```

### Test 4: CORS Configuration

```bash
# Test CORS headers
echo "Testing CORS..."
curl -H "Origin: https://evil.com" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS https://localhost/api/data -k -I
# Expected: No Access-Control-Allow-Origin header or restricted to trusted domains
```

### Test 5: Rate Limiting

```bash
# Test API rate limiting
echo "Testing API rate limiting..."
for i in {1..50}; do
  curl -X GET https://localhost/api/data -k \
    -H "Authorization: Bearer $TOKEN" \
    -w "%{http_code}\n" -o /dev/null -s
done
# Expected: 429 status codes after threshold
```

### Test 6: TLS/SSL Configuration

```bash
# Test SSL configuration
echo "Testing SSL/TLS..."
nmap --script ssl-enum-ciphers -p 443 localhost

# Test with SSL Labs (for public domains)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com

# Test HTTP to HTTPS redirect
curl -I http://localhost/
# Expected: 301 redirect to https://
```

### Test 7: Container Security

```bash
# Test 7.1: Verify non-root user
docker exec mcp-server-manager whoami
# Expected: mcpuser (not root)

# Test 7.2: Verify read-only filesystem
docker exec mcp-server-manager touch /test.txt
# Expected: Permission denied

# Test 7.3: Check security options
docker inspect mcp-server-manager | jq '.[0].HostConfig.SecurityOpt'
# Expected: ["no-new-privileges:true"]
```

### Test 8: Sensitive Data Exposure

```bash
# Test for exposed sensitive files
echo "Testing sensitive file access..."
curl https://localhost/.env -k
curl https://localhost/.git/config -k
curl https://localhost/backup.sql -k
curl https://localhost/config.yaml -k
# Expected: All should return 404 or 403

# Test for server information disclosure
curl -I https://localhost/ -k | grep -i server
# Expected: No detailed version information
```

---

## Automated Security Testing Script

Save as `security-test.sh`:

```bash
#!/bin/bash

# Security Test Suite for MCP Server
# Run: ./security-test.sh https://localhost

URL=${1:-https://localhost}
RESULTS_FILE="security-test-results-$(date +%Y%m%d-%H%M%S).log"

echo "Starting Security Tests for $URL" | tee $RESULTS_FILE
echo "================================" | tee -a $RESULTS_FILE

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
run_test() {
    local test_name=$1
    local command=$2
    local expected=$3
    
    echo -e "\n${YELLOW}Testing: $test_name${NC}" | tee -a $RESULTS_FILE
    result=$(eval $command 2>&1)
    
    if [[ $result == *"$expected"* ]]; then
        echo -e "${GREEN}✓ PASS${NC}" | tee -a $RESULTS_FILE
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}" | tee -a $RESULTS_FILE
        echo "Expected: $expected" | tee -a $RESULTS_FILE
        echo "Got: $result" | tee -a $RESULTS_FILE
        return 1
    fi
}

# Security Header Tests
run_test "X-Frame-Options Header" \
    "curl -sI $URL -k | grep -i x-frame-options" \
    "DENY"

run_test "X-Content-Type-Options Header" \
    "curl -sI $URL -k | grep -i x-content-type-options" \
    "nosniff"

run_test "Strict-Transport-Security Header" \
    "curl -sI $URL -k | grep -i strict-transport-security" \
    "max-age="

run_test "Content-Security-Policy Header" \
    "curl -sI $URL -k | grep -i content-security-policy" \
    "default-src"

# Authentication Tests
run_test "API requires authentication" \
    "curl -s -o /dev/null -w '%{http_code}' $URL/api/servers -k" \
    "401"

# Rate Limiting Tests
echo -e "\n${YELLOW}Testing Rate Limiting...${NC}" | tee -a $RESULTS_FILE
for i in {1..15}; do
    response=$(curl -s -o /dev/null -w '%{http_code}' $URL/api/data -k)
    if [ "$response" = "429" ]; then
        echo -e "${GREEN}✓ Rate limiting active at request $i${NC}" | tee -a $RESULTS_FILE
        break
    fi
done

# Sensitive File Tests
sensitive_files=(".env" ".git/config" "backup.sql" "config.yml" "/etc/passwd")
for file in "${sensitive_files[@]}"; do
    run_test "Block access to $file" \
        "curl -s -o /dev/null -w '%{http_code}' $URL/$file -k" \
        "404\|403"
done

# HTTP Methods Test
run_test "Block TRACE method" \
    "curl -X TRACE -s -o /dev/null -w '%{http_code}' $URL -k" \
    "405\|404"

# HTTPS Redirect Test
if [[ $URL == https://* ]]; then
    http_url=${URL/https/http}
    run_test "HTTP to HTTPS redirect" \
        "curl -s -o /dev/null -w '%{http_code}' $http_url" \
        "301\|302"
fi

echo -e "\n================================" | tee -a $RESULTS_FILE
echo "Security tests completed. Results saved to $RESULTS_FILE" | tee -a $RESULTS_FILE

# Count pass/fail
passes=$(grep -c "✓ PASS" $RESULTS_FILE)
fails=$(grep -c "✗ FAIL" $RESULTS_FILE)

echo -e "\nSummary: ${GREEN}$passes passed${NC}, ${RED}$fails failed${NC}" | tee -a $RESULTS_FILE

exit $fails
```

---

## Monitoring & Alerting Configuration

### Prometheus Alerts for Security

Create `docker/monitoring/prometheus/alerts/security-alerts.yml`:

```yaml
groups:
  - name: security
    interval: 30s
    rules:
      - alert: HighFailedLoginRate
        expr: rate(login_failures_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High failed login rate detected
          description: "Failed login rate is {{ $value }} per second"
      
      - alert: RateLimitExceeded
        expr: rate(rate_limit_exceeded_total[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Rate limit frequently exceeded
          description: "Rate limit exceeded {{ $value }} times per second"
      
      - alert: UnauthorizedAccessAttempt
        expr: rate(unauthorized_access_total[5m]) > 0.5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High unauthorized access attempts
          description: "{{ $value }} unauthorized attempts per second"
      
      - alert: SSLCertificateExpiringSoon
        expr: ssl_certificate_expiry_days < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: SSL certificate expiring soon
          description: "Certificate expires in {{ $value }} days"
```

### Grafana Dashboard for Security Metrics

Import this JSON to Grafana for security monitoring:

```json
{
  "dashboard": {
    "title": "Security Monitoring",
    "panels": [
      {
        "title": "Failed Login Attempts",
        "targets": [
          {
            "expr": "rate(login_failures_total[5m])"
          }
        ]
      },
      {
        "title": "Rate Limit Violations",
        "targets": [
          {
            "expr": "rate(rate_limit_exceeded_total[5m])"
          }
        ]
      },
      {
        "title": "Unauthorized Access Attempts",
        "targets": [
          {
            "expr": "rate(unauthorized_access_total[5m])"
          }
        ]
      },
      {
        "title": "API Response Times by Endpoint",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

---

## Security Compliance Checklist

### Pre-Production Checklist
- [ ] All default passwords changed
- [ ] Environment variables properly configured
- [ ] TLS certificates installed and valid
- [ ] Security headers configured
- [ ] Rate limiting tested
- [ ] Authentication/authorization working
- [ ] Input validation implemented
- [ ] CORS properly configured
- [ ] Container security hardened
- [ ] Monitoring and alerting active
- [ ] Backup and recovery tested
- [ ] Security tests passing
- [ ] Vulnerability scan completed
- [ ] Penetration testing performed
- [ ] Security documentation updated

### Weekly Security Tasks
- [ ] Review access logs for anomalies
- [ ] Check for security updates
- [ ] Verify backup integrity
- [ ] Review rate limit effectiveness
- [ ] Check certificate expiration
- [ ] Monitor security metrics

### Monthly Security Tasks
- [ ] Rotate secrets and API keys
- [ ] Update dependencies
- [ ] Review user access permissions
- [ ] Audit security configurations
- [ ] Test incident response procedures
- [ ] Update security documentation

---

## Incident Response Procedures

### 1. Suspected Security Breach
```bash
# Immediate actions
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale mcp-manager=0
# Preserves other services but stops the main application

# Collect evidence
docker logs mcp-server-manager > incident-$(date +%Y%m%d-%H%M%S).log
docker exec mcp-redis redis-cli --rdb /backup/redis-snapshot.rdb

# Analyze logs
grep -E "401|403|429" docker/nginx/logs/access.log | tail -100
```

### 2. DDoS Attack Response
```bash
# Enable stricter rate limiting
sed -i 's/rate=10r\/s/rate=1r\/s/g' docker/nginx/nginx.conf
docker-compose restart nginx

# Block specific IPs
iptables -A INPUT -s ATTACKER_IP -j DROP
```

### 3. Data Breach Response
```bash
# Rotate all secrets immediately
./scripts/rotate-secrets.sh

# Force logout all users
docker exec mcp-redis redis-cli FLUSHDB

# Generate incident report
./scripts/generate-incident-report.sh
```

---

## Additional Resources

- [OWASP Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)

---

## Support

For security issues, please report to: security@your-organization.com
Do not create public issues for security vulnerabilities.