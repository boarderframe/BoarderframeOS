# Production Deployment Guide for MCP Server Manager

## Overview

This guide covers the production deployment of MCP Server Manager with comprehensive security hardening, monitoring, and intrusion detection capabilities.

## Architecture Components

### Core Services
- **MCP Manager**: Main application with security hardening
- **Redis**: Secure session storage and caching
- **Nginx**: Reverse proxy with security headers and rate limiting
- **Open WebUI**: Secure chat interface

### Monitoring Stack
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Monitoring dashboards and visualization
- **Node Exporter**: Host metrics
- **CAdvisor**: Container resource monitoring
- **Redis Exporter**: Database metrics
- **Blackbox Exporter**: External service monitoring

### Security Stack
- **Falco**: Runtime security monitoring
- **Suricata**: Network intrusion detection
- **Elasticsearch**: Security log storage and analysis
- **Filebeat**: Centralized log collection
- **Kibana**: Security analytics dashboard

## Security Features

### Container Security
- Non-root user execution
- Read-only filesystems
- Capability dropping
- Resource limits and OOM handling
- Security contexts and AppArmor profiles
- Network isolation

### Network Security
- TLS/SSL encryption
- Security headers (HSTS, CSP, XSS protection)
- Rate limiting and DDoS protection
- CORS configuration
- Firewall rules

### Monitoring & Detection
- Runtime security monitoring with Falco
- Network intrusion detection with Suricata
- Vulnerability scanning with Trivy
- Log analysis and SIEM capabilities
- Automated alerting and incident response

## Quick Start

### 1. Environment Setup

```bash
# Copy and configure environment variables
cp docker/.env.production.template docker/.env.production

# Edit the configuration file
nano docker/.env.production
```

**Critical Variables to Configure:**
- `WEBUI_SECRET_KEY`: 32+ character random string
- `GRAFANA_ADMIN_PASSWORD`: Strong password
- `REDIS_PASSWORD`: Strong password
- `JWT_SECRET`: 64+ character random string
- `SSL_DOMAIN`: Your domain name
- `CORS_ORIGINS`: Trusted domain whitelist

### 2. SSL Certificate Setup

```bash
# Generate self-signed certificates (for testing)
mkdir -p docker/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/key.pem \
  -out docker/nginx/ssl/cert.pem

# For production, use Let's Encrypt or your CA certificates
```

### 3. Production Deployment

```bash
# Navigate to docker directory
cd docker/

# Run security validation and deploy
./deploy-production.sh production

# Or deploy with specific options
DRY_RUN=true ./deploy-production.sh production  # Test run
FORCE_DEPLOY=true ./deploy-production.sh production  # Skip security scans
```

### 4. Deploy with Security Monitoring

```bash
# Deploy core services + security monitoring
docker-compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               -f docker-compose.security.yml \
               --profile monitoring \
               --profile security \
               up -d
```

## Configuration Files

### Core Configuration
- `docker-compose.yml` - Base service definitions
- `docker-compose.prod.yml` - Production overrides with security hardening
- `docker-compose.security.yml` - Security monitoring stack
- `Dockerfile` - Hardened container image
- `.env.production.template` - Environment variable template

### Security Configuration
- `.dockerscan.yml` - Security scanning configuration
- `monitoring/falco/falco.yaml` - Runtime security monitoring
- `monitoring/filebeat/filebeat.yml` - Log collection and processing
- `monitoring/blackbox/config.yml` - External service monitoring
- `nginx/nginx-secure.conf` - Secure reverse proxy configuration

## Security Hardening Features

### Container Hardening
```yaml
# Resource limits
resources:
  limits:
    cpus: '1.0'
    memory: 512M
    pids: 100
  reservations:
    cpus: '0.5'
    memory: 256M

# Security options
security_opt:
  - no-new-privileges:true
  - apparmor:docker-default
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE

# OOM handling
oom_kill_disable: false
oom_score_adj: 100
memswap_limit: 512M
mem_swappiness: 10
```

### Network Security
```nginx
# Security headers
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-$request_id';" always;

# Rate limiting
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=3r/m;
```

## Monitoring and Alerting

### Service Endpoints
- **MCP Manager**: http://localhost:8080
- **Open WebUI**: http://localhost:3000
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601 (with security stack)
- **Falco UI**: http://localhost:2802 (with security stack)

### Key Metrics
- Container resource usage (CPU, memory, disk)
- Application performance (latency, throughput, errors)
- Security events (intrusions, anomalies, vulnerabilities)
- Network traffic analysis
- System health indicators

### Alert Rules
- Service downtime detection
- High resource usage warnings
- Security incident alerts
- Performance degradation notifications
- Certificate expiration warnings

## Security Scanning

### Automated Scanning
The deployment script includes:
- Container vulnerability scanning with Trivy
- Dockerfile best practices with Hadolint
- Custom security checks for secrets and misconfigurations
- Runtime security monitoring with Falco

### Manual Security Validation
```bash
# Run comprehensive security scan
trivy image --severity HIGH,CRITICAL mcp-server-manager:latest

# Check container security
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/docker-bench-security

# Validate network security
nmap -sS -O localhost
```

## Backup and Recovery

### Automated Backups
```bash
# Enable backup service
docker-compose --profile backup up -d backup-service

# Manual backup
docker exec mcp-backup-service /backup.sh
```

### Recovery Procedures
```bash
# Restore from backup
docker run --rm -v backup_data:/backup -v mcp_redis_data:/restore \
  alpine tar xzf /backup/redis_data.tar.gz -C /restore

# Restart services
docker-compose restart
```

## Performance Tuning

### Resource Optimization
- Container resource limits prevent resource exhaustion
- OOM handling ensures graceful degradation
- Connection pooling and caching reduce latency
- Gzip compression reduces bandwidth usage

### Scaling Considerations
- Horizontal scaling with Docker Swarm or Kubernetes
- Load balancing with multiple MCP Manager replicas
- Redis clustering for high availability
- CDN integration for static assets

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   docker-compose logs mcp-manager
   
   # Verify configuration
   docker-compose config
   ```

2. **SSL/TLS Issues**
   ```bash
   # Test certificate
   openssl x509 -in docker/nginx/ssl/cert.pem -text -noout
   
   # Check nginx configuration
   docker exec mcp-nginx nginx -t
   ```

3. **Security Alerts**
   ```bash
   # Check Falco events
   docker logs mcp-falco
   
   # Review security dashboard
   # Open Kibana at http://localhost:5601
   ```

4. **Performance Issues**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check application metrics
   # Open Grafana at http://localhost:3001
   ```

### Log Locations
- Application logs: `/var/log/mcp-deploy.log`
- Container logs: `docker logs <container_name>`
- Security events: Elasticsearch indices `mcp-security-*`
- System logs: `/var/log/syslog`

## Maintenance

### Regular Tasks
- Update base images monthly
- Run security scans weekly
- Review and rotate secrets quarterly
- Update SSL certificates before expiration
- Monitor disk usage and clean old logs

### Health Checks
```bash
# Service health
curl http://localhost:8080/health

# Security monitoring
curl http://localhost:2802/api/v1/events

# Metrics collection
curl http://localhost:9090/-/healthy
```

## Security Best Practices

1. **Secrets Management**
   - Use strong, unique passwords
   - Rotate secrets regularly
   - Never commit secrets to version control
   - Use environment variables for configuration

2. **Network Security**
   - Enable SSL/TLS for all communications
   - Use firewall rules to restrict access
   - Implement rate limiting and DDoS protection
   - Monitor network traffic for anomalies

3. **Container Security**
   - Run containers as non-root users
   - Use read-only filesystems where possible
   - Drop unnecessary capabilities
   - Regularly update base images

4. **Monitoring**
   - Enable comprehensive logging
   - Set up alerting for security events
   - Monitor resource usage trends
   - Regular security audits and penetration testing

## Support and Troubleshooting

For additional support:
1. Check the logs for error messages
2. Verify configuration files
3. Test network connectivity
4. Review security alerts
5. Consult the monitoring dashboards

Remember to keep all components updated and follow security best practices for production deployments.