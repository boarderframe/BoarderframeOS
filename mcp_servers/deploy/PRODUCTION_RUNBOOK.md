# MCP-UI Production Operations Runbook

## Overview

This runbook provides comprehensive operational procedures for the MCP-UI production system, including deployment, monitoring, troubleshooting, and disaster recovery.

## System Architecture

### Components
- **Frontend**: React/Svelte application served by Nginx
- **Backend**: FastAPI Python application
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis ElastiCache cluster
- **Monitoring**: Prometheus, Grafana, Jaeger
- **Logging**: OpenSearch with Logstash/Fluentd
- **Load Balancer**: AWS Application Load Balancer
- **Container Platform**: Amazon EKS (Kubernetes)

### Infrastructure
- **AWS Region**: us-west-2 (primary), us-east-1 (DR)
- **Kubernetes Version**: 1.28
- **Node Types**: t3.large, t3.xlarge (production)
- **Auto-scaling**: 3-20 nodes based on demand

## Production URLs

- **Main Application**: https://mcp-ui.example.com
- **API Endpoints**: https://api.mcp-ui.example.com
- **Grafana Dashboard**: https://grafana.mcp-ui.example.com
- **Jaeger Tracing**: https://jaeger.mcp-ui.example.com
- **Prometheus**: https://prometheus.mcp-ui.example.com (internal)
- **Status Page**: https://status.mcp-ui.example.com

## Deployment Procedures

### 1. Production Deployment

**Prerequisites:**
- AWS CLI configured with production access
- kubectl configured for production cluster
- Terraform >= 1.6.0
- Helm >= 3.13.0

**Standard Deployment:**
```bash
# Clone repository
git clone <repository-url>
cd mcp-servers

# Deploy using automated script
./deploy/scripts/production-deployment.sh

# Or deploy specific environment
./deploy/scripts/production-deployment.sh -e production -r us-west-2
```

**Manual Deployment Steps:**
```bash
# 1. Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name mcp-ui-production

# 2. Deploy infrastructure
cd deploy/terraform
terraform init
terraform plan -var="environment=production"
terraform apply -var="environment=production"

# 3. Deploy Kubernetes resources
kubectl apply -f ../k8s/namespace.yaml
kubectl apply -f ../k8s/mcp-autoscaling.yaml
kubectl apply -f ../k8s/mcp-manager-deployment.yaml
kubectl apply -f ../k8s/mcp-ingress.yaml
kubectl apply -f ../k8s/monitoring-stack.yaml

# 4. Verify deployment
kubectl get pods -n mcp-ui
kubectl get ingress -n mcp-ui
```

### 2. Blue-Green Deployment

For zero-downtime deployments:

```bash
# Deploy green environment
helm upgrade mcp-ui-green ./helm/mcp-ui \
  --set deployment.version=green \
  --set backend.image=new-image:tag \
  --namespace mcp-ui

# Test green environment
kubectl exec -n mcp-ui deployment/mcp-manager-green -- curl -f http://localhost:8000/health

# Switch traffic to green
kubectl patch service mcp-manager-service -n mcp-ui \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Clean up blue environment
helm uninstall mcp-ui-blue --namespace mcp-ui
```

### 3. Rollback Procedure

**Automatic Rollback:**
```bash
kubectl rollout undo deployment/mcp-manager -n mcp-ui
kubectl rollout undo deployment/mcp-frontend -n mcp-ui
```

**Manual Rollback to Specific Version:**
```bash
# List previous versions
kubectl rollout history deployment/mcp-manager -n mcp-ui

# Rollback to specific revision
kubectl rollout undo deployment/mcp-manager -n mcp-ui --to-revision=2

# Verify rollback
kubectl rollout status deployment/mcp-manager -n mcp-ui
```

## Monitoring and Alerting

### 1. Key Metrics to Monitor

**Application Metrics:**
- Request rate: `rate(http_requests_total[5m])`
- Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
- Response time: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- Active connections: `mcp_active_connections`

**Infrastructure Metrics:**
- CPU utilization: `rate(container_cpu_usage_seconds_total[5m])`
- Memory usage: `container_memory_usage_bytes`
- Pod readiness: `kube_pod_status_ready`
- Node availability: `kube_node_status_condition{condition="Ready"}`

**Database Metrics:**
- Connection count: `postgresql_stat_database_numbackends`
- Query performance: `postgresql_stat_statements_mean_time`
- Replication lag: `postgresql_replication_lag`

### 2. Alert Thresholds

**Critical Alerts (Page immediately):**
- Error rate > 5% for 2 minutes
- Response time P95 > 5 seconds for 3 minutes
- Pod crash looping
- Database connection failure
- SSL certificate expiry < 24 hours

**Warning Alerts (Investigate within hours):**
- Error rate > 1% for 5 minutes
- Response time P95 > 2 seconds for 5 minutes
- CPU usage > 80% for 5 minutes
- Memory usage > 85% for 5 minutes
- Disk usage > 80%

### 3. Grafana Dashboards

**Main Dashboard Panels:**
1. Service Health Overview
2. Request Volume and Error Rates
3. Response Time Percentiles
4. Resource Utilization
5. Database Performance
6. Cache Hit Rates
7. External Dependencies Status

**Alert Manager Configuration:**
- Slack notifications: #mcp-ui-alerts (warnings), #mcp-ui-critical (critical)
- Email notifications: ops-team@example.com (critical only)
- PagerDuty integration: On-call rotation for critical alerts

## Troubleshooting Guide

### 1. High Error Rate

**Symptoms:**
- 5xx errors in application logs
- High error rate in Grafana dashboard
- User reports of service unavailability

**Investigation Steps:**
```bash
# Check pod status
kubectl get pods -n mcp-ui -o wide

# Check application logs
kubectl logs -f deployment/mcp-manager -n mcp-ui --tail=100

# Check recent events
kubectl get events -n mcp-ui --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n mcp-ui
kubectl top nodes
```

**Common Causes and Solutions:**
1. **Database connection issues:**
   - Check database connectivity: `kubectl exec -n mcp-ui deployment/mcp-manager -- pg_isready -h $DB_HOST`
   - Check connection pool: Monitor `postgresql_stat_activity`
   - Scale database if needed

2. **Memory pressure:**
   - Check pod memory limits and requests
   - Scale horizontally: `kubectl scale deployment mcp-manager --replicas=5 -n mcp-ui`
   - Check for memory leaks in application logs

3. **External dependency failures:**
   - Check Redis connectivity: `kubectl exec -n mcp-ui deployment/mcp-manager -- redis-cli -h $REDIS_HOST ping`
   - Review external API integrations
   - Implement circuit breaker patterns

### 2. Slow Response Times

**Investigation:**
```bash
# Check Jaeger traces
# Access https://jaeger.mcp-ui.example.com and search for slow traces

# Check database query performance
kubectl exec -n mcp-ui-data deployment/postgresql -- psql -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Check application metrics
# Use Grafana dashboard to identify bottlenecks
```

**Solutions:**
1. **Database optimization:**
   - Add missing indexes
   - Optimize slow queries
   - Scale read replicas

2. **Application optimization:**
   - Enable response caching
   - Optimize database queries
   - Implement connection pooling

3. **Infrastructure scaling:**
   - Increase CPU/memory limits
   - Scale horizontally
   - Enable auto-scaling

### 3. Pod Crashes or Restarts

**Investigation:**
```bash
# Check pod status and restarts
kubectl get pods -n mcp-ui

# Check pod events
kubectl describe pod <pod-name> -n mcp-ui

# Check previous container logs
kubectl logs <pod-name> -n mcp-ui --previous

# Check resource limits
kubectl describe deployment mcp-manager -n mcp-ui
```

**Common Causes:**
1. **OOMKilled (Out of Memory):**
   - Increase memory limits
   - Check for memory leaks
   - Optimize application memory usage

2. **Liveness probe failures:**
   - Check application health endpoint
   - Adjust probe timing
   - Fix application health checks

3. **Resource constraints:**
   - Check node capacity
   - Scale cluster if needed
   - Adjust resource requests/limits

### 4. Database Issues

**Connection Issues:**
```bash
# Test database connectivity
kubectl run db-test --image=postgres:15 --rm -it --restart=Never -n mcp-ui \
  -- psql -h <db-host> -U <username> -d <database>

# Check connection pool status
kubectl exec -n mcp-ui deployment/mcp-manager -- python -c "
import psycopg2.pool
# Check connection pool status
"
```

**Performance Issues:**
```bash
# Check slow queries
kubectl exec -n mcp-ui-data deployment/postgresql -- psql -c "
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
WHERE mean_time > 1000
ORDER BY mean_time DESC;"

# Check database locks
kubectl exec -n mcp-ui-data deployment/postgresql -- psql -c "
SELECT * FROM pg_locks 
WHERE NOT granted;"

# Check replication status
kubectl exec -n mcp-ui-data deployment/postgresql -- psql -c "
SELECT * FROM pg_stat_replication;"
```

## Backup and Recovery

### 1. Automated Backups

**Database Backups:**
- **Schedule**: Daily at 2 AM UTC
- **Retention**: 30 days for production, 7 days for staging
- **Location**: S3 bucket with cross-region replication
- **Monitoring**: CronJob status monitored via Prometheus

**Configuration Backups:**
- **Schedule**: Daily at 1 AM UTC
- **Content**: ConfigMaps, Secrets metadata, RBAC
- **Location**: S3 bucket with versioning enabled

### 2. Manual Backup Procedures

**Database Backup:**
```bash
# Create manual database backup
kubectl create job --from=cronjob/postgres-backup manual-backup-$(date +%Y%m%d) -n mcp-ui-backup

# Wait for completion
kubectl wait --for=condition=complete job/manual-backup-$(date +%Y%m%d) -n mcp-ui-backup --timeout=600s

# Check backup in S3
aws s3 ls s3://mcp-ui-backups-production/database/
```

**Application State Backup:**
```bash
# Backup current deployments
kubectl get deployment,service,ingress,configmap -n mcp-ui -o yaml > mcp-ui-backup-$(date +%Y%m%d).yaml

# Backup secrets metadata (not values)
kubectl get secrets -n mcp-ui -o yaml | sed 's/data:/# data:/g' > secrets-metadata-$(date +%Y%m%d).yaml
```

### 3. Recovery Procedures

**Database Recovery:**
```bash
# List available backups
aws s3 ls s3://mcp-ui-backups-production/database/

# Restore from specific backup
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: database-restore-$(date +%s)
  namespace: mcp-ui-backup
spec:
  template:
    spec:
      containers:
      - name: restore
        image: postgres:15
        env:
        - name: BACKUP_FILE
          value: "postgres_backup_20240115_020000.sql.gz"
        - name: S3_BUCKET
          value: "mcp-ui-backups-production"
        command:
        - /bin/bash
        - -c
        - |
          aws s3 cp s3://\$S3_BUCKET/database/\$BACKUP_FILE /tmp/
          gunzip /tmp/\$BACKUP_FILE
          psql -h \$PGHOST -U \$PGUSER -d \$PGDATABASE < /tmp/\${BACKUP_FILE%.gz}
      restartPolicy: Never
EOF
```

**Application Recovery:**
```bash
# Restore from backup file
kubectl apply -f mcp-ui-backup-20240115.yaml

# Verify restoration
kubectl get pods -n mcp-ui
kubectl get services -n mcp-ui
```

## Security Procedures

### 1. Certificate Management

**SSL Certificate Monitoring:**
```bash
# Check certificate expiry
kubectl get certificates -n mcp-ui -o custom-columns=NAME:.metadata.name,READY:.status.conditions[0].status,SECRET:.spec.secretName,ISSUER:.spec.issuerRef.name,EXPIRY:.status.notAfter

# Manual certificate renewal
kubectl delete certificate mcp-ui-tls-cert -n mcp-ui
kubectl apply -f deploy/k8s/cert-manager.yaml
```

**Certificate Alerts:**
- Warning: 7 days before expiry
- Critical: 24 hours before expiry
- Failed renewal: Immediate notification

### 2. Security Scanning

**Container Image Scanning:**
```bash
# Scan images with Trivy
trivy image ghcr.io/mcp-ui/backend:latest
trivy image ghcr.io/mcp-ui/frontend:latest

# Check for vulnerabilities in running containers
kubectl get vulnerabilityreports -A
```

**Security Policy Enforcement:**
- Pod Security Standards enforced
- Network policies configured
- RBAC with principle of least privilege
- Resource limits and security contexts mandatory

### 3. Access Management

**kubectl Access:**
- Production access requires MFA
- All access logged and audited
- Role-based access control (RBAC)
- Regular access reviews

**AWS Access:**
- Cross-account roles for deployment
- CloudTrail logging enabled
- GuardDuty monitoring active
- Security Hub compliance checks

## Performance Optimization

### 1. Application Performance

**Database Optimization:**
```sql
-- Add indexes for frequently queried columns
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_servers_status ON mcp_servers(status, created_at);

-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM mcp_servers WHERE status = 'active';

-- Update table statistics
ANALYZE;
```

**Cache Optimization:**
```bash
# Redis cache hit rate monitoring
kubectl exec -n mcp-ui-data deployment/redis -- redis-cli info stats | grep hit_rate

# Optimize cache configuration
kubectl patch configmap redis-config -n mcp-ui-data --patch '
data:
  redis.conf: |
    maxmemory-policy allkeys-lru
    timeout 300
    tcp-keepalive 300
'
```

### 2. Infrastructure Scaling

**Horizontal Pod Autoscaling:**
```bash
# Check current HPA status
kubectl get hpa -n mcp-ui

# Modify HPA targets
kubectl patch hpa mcp-manager-hpa -n mcp-ui --patch '
spec:
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
'
```

**Cluster Autoscaling:**
```bash
# Check cluster autoscaler logs
kubectl logs -f deployment/cluster-autoscaler -n kube-system

# Check node utilization
kubectl top nodes

# Scale node group manually if needed
aws eks update-nodegroup-config \
  --cluster-name mcp-ui-production \
  --nodegroup-name mcp-ui-nodes-production \
  --scaling-config minSize=3,maxSize=25,desiredSize=5
```

## Emergency Procedures

### 1. Service Degradation

**Immediate Actions:**
1. Check status dashboard: https://status.mcp-ui.example.com
2. Review Grafana alerts: https://grafana.mcp-ui.example.com
3. Check recent deployments: `kubectl rollout history deployment/mcp-manager -n mcp-ui`
4. Scale up if resource constrained: `kubectl scale deployment mcp-manager --replicas=10 -n mcp-ui`

**Communication:**
1. Post in #incidents Slack channel
2. Update status page
3. Create incident in PagerDuty
4. Notify stakeholders via email

### 2. Database Emergency

**Read-Only Mode:**
```bash
# Enable read-only mode in application
kubectl patch configmap mcp-config -n mcp-ui --patch '
data:
  mcp.json: |
    {
      "database": {
        "read_only": true
      }
    }
'

# Restart application to pick up config
kubectl rollout restart deployment/mcp-manager -n mcp-ui
```

**Failover to Read Replica:**
```bash
# Update database connection to point to read replica
kubectl patch secret mcp-secrets -n mcp-ui --patch '
data:
  database-url: <base64-encoded-replica-url>
'

# Restart application
kubectl rollout restart deployment/mcp-manager -n mcp-ui
```

### 3. Complete Service Outage

**DR Site Activation:**
1. Activate disaster recovery runbook: `/deploy/k8s/backup-disaster-recovery.yaml`
2. Deploy to secondary region:
   ```bash
   ./deploy/scripts/production-deployment.sh -r us-east-1 -e production-dr
   ```
3. Update DNS to point to DR site
4. Communicate with users and stakeholders

## Maintenance Procedures

### 1. Planned Maintenance

**Maintenance Window:** Sunday 2-6 AM UTC (low traffic period)

**Pre-maintenance Checklist:**
- [ ] Announce maintenance 48 hours in advance
- [ ] Create backup before changes
- [ ] Prepare rollback plan
- [ ] Test changes in staging environment
- [ ] Update status page

**During Maintenance:**
```bash
# Enable maintenance mode
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: maintenance-config
  namespace: mcp-ui
data:
  maintenance.html: |
    <html>
    <body>
      <h1>Maintenance in Progress</h1>
      <p>We're performing scheduled maintenance. Please check back soon.</p>
    </body>
    </html>
EOF

# Update ingress to serve maintenance page
kubectl patch ingress mcp-ui-ingress -n mcp-ui --patch '
metadata:
  annotations:
    nginx.ingress.kubernetes.io/custom-http-errors: "503"
    nginx.ingress.kubernetes.io/default-backend: maintenance-service
'
```

### 2. Security Updates

**Critical Security Patches:**
1. Test patches in staging environment
2. Schedule emergency maintenance if needed
3. Apply patches using blue-green deployment
4. Perform security scan after updates

**Regular Security Updates:**
- Container base image updates: Monthly
- Kubernetes version updates: Quarterly
- Application dependency updates: Weekly

### 3. Capacity Planning

**Monthly Review:**
- Resource utilization trends
- Performance metrics analysis
- Cost optimization opportunities
- Scaling recommendations

**Quarterly Planning:**
- Infrastructure capacity planning
- Budget reviews and forecasting
- Technology stack updates
- Security audit and compliance

## Contact Information

### On-Call Rotation
- **Primary**: +1-555-ONCALL-1
- **Secondary**: +1-555-ONCALL-2
- **Escalation**: +1-555-MANAGER

### Team Contacts
- **DevOps Lead**: devops-lead@example.com
- **Product Owner**: product@example.com
- **Security Team**: security@example.com
- **Infrastructure Team**: infrastructure@example.com

### External Support
- **AWS Support**: Enterprise Support Portal
- **CloudFlare Support**: Priority Support
- **Database Vendor**: 24/7 Support Hotline

## Documentation Links

- **API Documentation**: https://api.mcp-ui.example.com/docs
- **Architecture Diagrams**: /docs/architecture/
- **Terraform Documentation**: /deploy/terraform/README.md
- **Kubernetes Manifests**: /deploy/k8s/README.md
- **Monitoring Setup**: /deploy/monitoring/README.md

---

**Last Updated**: $(date +"%Y-%m-%d")
**Version**: 1.0
**Maintained By**: DevOps Team

*This runbook is a living document. Please update it when procedures change.*