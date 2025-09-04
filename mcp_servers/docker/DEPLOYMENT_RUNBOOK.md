# MCP Server Manager Deployment Runbook

## Overview
This runbook provides step-by-step procedures for deploying, monitoring, and troubleshooting the MCP Server Manager application.

## Quick Start

### Docker Compose Deployment
```bash
# 1. Clone repository and navigate to docker directory
cd /path/to/mcp-server-manager/docker

# 2. Copy and configure environment file
cp .env.example .env
# Edit .env with your configuration

# 3. Deploy (development)
./deploy.sh deploy development

# 4. Deploy (production)
./deploy.sh deploy production
```

### Kubernetes Deployment
```bash
# 1. Apply namespace and RBAC
kubectl apply -f k8s/namespace.yaml

# 2. Create secrets
kubectl create secret generic mcp-secrets \
  --from-literal=redis-password=your-redis-password \
  --from-literal=webui-secret-key=your-secret-key \
  -n mcp-server-manager

# 3. Deploy services
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/mcp-manager.yaml
kubectl apply -f k8s/ingress.yaml
```

## Pre-Deployment Checklist

### Infrastructure Requirements
- [ ] Docker Engine 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] Minimum 4GB RAM available
- [ ] Minimum 10GB disk space available
- [ ] Network ports 80, 443, 8080, 3000, 6379 available
- [ ] SSL certificates configured (production)

### Security Requirements
- [ ] Environment variables configured in `.env`
- [ ] Strong passwords set for all services
- [ ] SSL/TLS certificates valid and not expiring soon
- [ ] Firewall rules configured
- [ ] Backup storage configured

### Configuration Validation
- [ ] Environment file syntax valid
- [ ] Docker compose configuration valid: `docker-compose config`
- [ ] Health check endpoints accessible
- [ ] Monitoring alerts configured

## Deployment Procedures

### Standard Deployment

1. **Pre-deployment backup**
   ```bash
   ./backup.sh full
   ```

2. **Deploy application**
   ```bash
   ./deploy.sh deploy production
   ```

3. **Verify deployment**
   ```bash
   ./health-check.sh
   ```

4. **Post-deployment testing**
   ```bash
   # Test API endpoints
   curl -f http://localhost:8080/health
   curl -f http://localhost:8080/api/v1/status
   
   # Test WebUI
   curl -f http://localhost:3000/health
   
   # Test monitoring
   curl -f http://localhost:9090/-/healthy
   curl -f http://localhost:3001/api/health
   ```

### Zero-Downtime Deployment

1. **Scale up new instances**
   ```bash
   docker-compose up -d --scale mcp-manager=3
   ```

2. **Health check new instances**
   ```bash
   ./health-check.sh
   ```

3. **Update load balancer configuration**
   ```bash
   docker-compose exec nginx nginx -s reload
   ```

4. **Scale down old instances**
   ```bash
   docker-compose up -d --scale mcp-manager=2
   ```

### Emergency Rollback

```bash
# Quick rollback to previous version
./deploy.sh rollback

# Or restore from backup
./backup.sh restore backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

## Monitoring and Alerting

### Health Check Commands
```bash
# Full system health check
./health-check.sh

# Check specific components
./health-check.sh containers  # Container status only
./health-check.sh services    # Service endpoints only
./health-check.sh system      # System resources only
```

### Key Metrics to Monitor

#### Application Metrics
- **Response Time**: P95 < 1s, P99 < 2s
- **Error Rate**: < 1% 5xx errors
- **Throughput**: Monitor requests/second
- **Active Users**: Monitor concurrent sessions

#### Infrastructure Metrics
- **CPU Usage**: < 80% average
- **Memory Usage**: < 80% of allocated
- **Disk Space**: < 80% used
- **Network**: Monitor bandwidth and latency

#### Service-Specific Metrics
- **Redis**: Memory usage, connection count, hit rate
- **Ollama**: GPU usage, model loading time
- **Nginx**: Request rate, error rate, response time

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Disk Space | > 80% | > 95% |
| Error Rate | > 2% | > 5% |
| Response Time | > 2s | > 5s |

## Troubleshooting Guide

### Common Issues

#### Service Won't Start
```bash
# Check container logs
docker-compose logs mcp-manager

# Check container status
docker-compose ps

# Check resource usage
docker stats

# Check network connectivity
docker-compose exec mcp-manager ping redis
```

#### High Memory Usage
```bash
# Check memory usage by container
docker stats --no-stream

# Check for memory leaks
docker-compose exec mcp-manager cat /proc/meminfo

# Restart service if needed
docker-compose restart mcp-manager
```

#### Database Connection Issues
```bash
# Test Redis connectivity
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis

# Verify Redis configuration
docker-compose exec redis redis-cli config get "*"
```

#### SSL Certificate Issues
```bash
# Check certificate expiry
openssl x509 -in /path/to/cert.pem -text -noout | grep "Not After"

# Test SSL configuration
openssl s_client -connect your-domain.com:443

# Renew Let's Encrypt certificate
certbot renew --dry-run
```

### Performance Optimization

#### Database Optimization
```bash
# Redis memory optimization
docker-compose exec redis redis-cli config set maxmemory-policy allkeys-lru

# Check Redis slow queries
docker-compose exec redis redis-cli slowlog get 10
```

#### Application Optimization
```bash
# Enable production optimizations
export NODE_ENV=production
export NODE_OPTIONS="--max-old-space-size=512"

# Monitor garbage collection
docker-compose exec mcp-manager node --expose-gc --trace-gc app.js
```

## Backup and Recovery

### Backup Procedures

#### Automated Daily Backup
```bash
# Add to crontab
0 2 * * * /path/to/mcp-server-manager/docker/backup.sh full
```

#### Manual Backup
```bash
# Full backup (all data and configs)
./backup.sh full

# Incremental backup (data only)
./backup.sh incremental
```

### Recovery Procedures

#### Full System Recovery
```bash
# 1. Stop all services
docker-compose down

# 2. Restore from backup
./backup.sh restore backups/backup_YYYYMMDD.tar.gz

# 3. Verify restoration
./health-check.sh
```

#### Partial Recovery (Database Only)
```bash
# 1. Stop application
docker-compose stop mcp-manager

# 2. Restore Redis data
docker cp backup/redis_dump.rdb mcp_redis_1:/data/

# 3. Restart services
docker-compose restart redis
docker-compose start mcp-manager
```

## Security Procedures

### Security Hardening Checklist
- [ ] All default passwords changed
- [ ] SSL/TLS enabled for all endpoints
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Network segmentation implemented
- [ ] Regular security updates applied
- [ ] Log monitoring enabled
- [ ] Intrusion detection configured

### Incident Response

#### Security Incident
1. **Immediate Actions**
   - Isolate affected systems
   - Stop data exfiltration
   - Preserve evidence

2. **Assessment**
   - Determine scope of breach
   - Identify compromised data
   - Document timeline

3. **Containment**
   - Patch vulnerabilities
   - Update access controls
   - Monitor for persistence

4. **Recovery**
   - Restore from clean backups
   - Implement additional controls
   - Resume normal operations

### Log Analysis
```bash
# Check application logs for errors
docker-compose logs mcp-manager | grep ERROR

# Check access logs for suspicious activity
docker-compose logs nginx | grep -E "(404|500|40[1-9])"

# Monitor authentication attempts
docker-compose logs open-webui | grep "auth"
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
- [ ] Check service health status
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Verify backup completion

#### Weekly
- [ ] Update security patches
- [ ] Review monitoring alerts
- [ ] Analyze performance metrics
- [ ] Test backup restoration

#### Monthly
- [ ] Security assessment
- [ ] Capacity planning review
- [ ] Update runbook procedures
- [ ] DR testing

### Update Procedures

#### Application Updates
```bash
# 1. Create backup
./backup.sh full

# 2. Pull latest images
docker-compose pull

# 3. Deploy with rolling update
docker-compose up -d

# 4. Verify update
./health-check.sh
```

#### Infrastructure Updates
```bash
# 1. Plan maintenance window
# 2. Notify users of downtime
# 3. Create full backup
# 4. Update infrastructure
# 5. Test all services
# 6. Resume normal operations
```

## Contact Information

### On-Call Procedures
- **Primary Contact**: admin@example.com
- **Secondary Contact**: ops@example.com
- **Escalation**: manager@example.com

### External Dependencies
- **Cloud Provider**: AWS/GCP/Azure Support
- **DNS Provider**: Cloudflare/Route53
- **Certificate Authority**: Let's Encrypt
- **Monitoring Service**: DataDog/New Relic

## Appendix

### Useful Commands
```bash
# View all container logs
docker-compose logs -f

# Execute shell in container
docker-compose exec mcp-manager /bin/sh

# Check container resource usage
docker stats

# View network configuration
docker-compose config

# Cleanup unused resources
docker system prune -a
```

### Configuration Files
- `docker-compose.yml` - Main compose configuration
- `docker-compose.prod.yml` - Production overrides
- `docker-compose.dev.yml` - Development overrides
- `.env` - Environment variables
- `nginx/nginx.conf` - Reverse proxy configuration
- `monitoring/prometheus/prometheus.yml` - Monitoring configuration

### External Documentation
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Redis Configuration](https://redis.io/documentation)

---

**Last Updated**: $(date)
**Version**: 1.0
**Maintainer**: DevOps Team