# MCP Server Manager - Docker Deployment

This directory contains a complete Docker-based deployment solution for the MCP (Model Context Protocol) Server Manager, including monitoring, AI integration, and production-ready configurations.

## 🏗️ Architecture

The deployment includes the following services:

- **MCP Manager**: Core application server (Node.js)
- **Redis**: Data storage, caching, and session management
- **Open WebUI**: Chat interface for AI interactions
- **Ollama**: Local LLM inference engine
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Monitoring dashboards and visualization
- **NGINX**: Load balancer and reverse proxy (production only)

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 5GB+ free disk space

### 1. Validation

First, validate your setup:

```bash
cd docker
./validate.sh
```

### 2. Configuration

Copy the environment template and customize:

```bash
cp .env.template .env
# Edit .env with your configuration
```

**Important**: Change default passwords and secrets in `.env` before production deployment!

### 3. Start Services

#### Development Mode
```bash
./start.sh
# or
./start.sh -e development
```

#### Production Mode
```bash
./start.sh -e production -b
```

### 4. Access Services

Once started, access the services at:

- **MCP Manager**: http://localhost:8080
- **Open WebUI**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin - change password!)
- **Redis**: localhost:6379

## 📁 File Structure

```
docker/
├── Dockerfile                 # Multi-stage production Dockerfile
├── docker-compose.yml        # Base compose configuration
├── docker-compose.prod.yml   # Production overrides
├── docker-compose.dev.yml    # Development overrides
├── .env.template             # Environment configuration template
├── start.sh                  # Deployment startup script
├── validate.sh               # Configuration validation script
├── deploy.sh                 # CI/CD deployment script
├── backup.sh                 # Backup automation script
├── health-check.sh           # Health monitoring script
├── nginx/
│   └── nginx.conf           # NGINX configuration
└── monitoring/
    ├── prometheus/
    │   ├── prometheus.yml   # Prometheus configuration
    │   └── alerts/
    │       └── mcp-alerts.yml
    └── grafana/            # Grafana dashboards
```

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Security (CHANGE THESE!)
WEBUI_SECRET_KEY=your-secret-key-change-this
GRAFANA_ADMIN_PASSWORD=admin-change-this-password
REDIS_PASSWORD=redis-secure-password-change-this

# Application
NODE_ENV=production
LOG_LEVEL=info
RATE_LIMIT_ENABLED=true

# Features
ENABLE_SIGNUP=false
SECURITY_AUDIT_ENABLED=true
```

### Resource Limits

Production resource limits are configured in `docker-compose.prod.yml`:

- **MCP Manager**: 1 CPU, 512MB RAM
- **Redis**: 0.5 CPU, 256MB RAM  
- **Ollama**: 2 CPU, 4GB RAM
- **Prometheus**: 0.5 CPU, 512MB RAM
- **Grafana**: 0.5 CPU, 256MB RAM

## 🔒 Security Features

### Container Security
- Non-root user execution
- Read-only root filesystems
- Security options: `no-new-privileges`, `apparmor`
- Minimal capability sets
- Isolated networks

### Application Security
- Rate limiting enabled
- Security audit logging
- Authentication required
- Secure session management
- HTTPS ready (with SSL certificates)

### Data Protection
- Encrypted connections between services
- Persistent volume encryption support
- Backup automation with retention policies
- Redis password protection

## 🔍 Monitoring & Observability

### Health Checks
All services include comprehensive health checks:
- HTTP endpoint monitoring
- Service dependency validation
- Resource utilization tracking
- Automatic restart on failure

### Metrics & Alerting
- **Prometheus**: Metrics collection from all services
- **Grafana**: Pre-configured dashboards for system monitoring
- **Alert Rules**: Automated alerts for service issues
- **Log Aggregation**: Centralized logging with retention

### Monitoring Endpoints
- Service health: `http://localhost:8080/health`
- Metrics: `http://localhost:8080/metrics`
- Prometheus: `http://localhost:9090`
- Grafana dashboards: `http://localhost:3001`

## 🚀 Deployment Modes

### Development Mode
- Hot reload enabled for code changes
- Debug logging active
- Relaxed security settings
- Development tools container
- Source code mounted as volumes

```bash
./start.sh -e development
```

### Production Mode
- Optimized resource allocation
- Enhanced security controls
- NGINX load balancer
- Backup automation
- Monitoring alerts enabled

```bash
./start.sh -e production -b
```

## 🔄 Operations

### Starting Services
```bash
# Standard start
./start.sh

# Force rebuild
./start.sh -b

# Clean start (removes volumes)
./start.sh -c

# Foreground mode (see logs)
./start.sh -f
```

### Managing Services
```bash
# View logs
docker-compose logs -f [service_name]

# Scale services
docker-compose up -d --scale mcp-manager=3

# Update services
docker-compose pull && docker-compose up -d

# Stop services
docker-compose down

# Complete cleanup
docker-compose down -v --remove-orphans
```

### Data Management
```bash
# Backup data
./backup.sh

# Restore from backup
./backup.sh restore <backup_file>

# View volume usage
docker system df -v
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts**: Check if ports 8080, 3000, 6379, 9090, 3001, 11434 are available
2. **Memory Issues**: Ensure at least 4GB RAM available for all services
3. **Permission Errors**: Check file permissions on mounted volumes
4. **Network Issues**: Verify Docker network configuration

### Debug Commands
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs -f mcp-manager

# Connect to service container
docker-compose exec mcp-manager sh

# Validate configuration
./validate.sh

# Network connectivity test
docker-compose exec mcp-manager ping redis
```

### Log Locations
- Application logs: `docker-compose logs mcp-manager`
- Redis logs: `docker-compose logs redis`
- NGINX logs: `./nginx/logs/`
- System logs: `docker system events`

## 📊 Performance Optimization

### Resource Monitoring
Monitor resource usage with:
```bash
# Container resource usage
docker stats

# System resource usage
docker system df

# Service performance
docker-compose top
```

### Scaling Guidelines
- **CPU**: Scale horizontally by increasing replicas
- **Memory**: Adjust limits in `docker-compose.prod.yml`
- **Storage**: Monitor volume usage and implement cleanup policies
- **Network**: Use load balancer for high-traffic scenarios

## 🔐 Production Checklist

Before deploying to production:

- [ ] Change all default passwords in `.env`
- [ ] Configure SSL certificates in `nginx/ssl/`
- [ ] Set up backup automation
- [ ] Configure monitoring alerts
- [ ] Review security settings
- [ ] Test disaster recovery procedures
- [ ] Set up log rotation
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Document emergency procedures

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs -f`
3. Validate configuration: `./validate.sh`
4. Check service health: `curl http://localhost:8080/health`

## 📚 Additional Resources

- [Docker Compose Reference](https://docs.docker.com/compose/)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Open WebUI Documentation](https://github.com/open-webui/open-webui)
- [Ollama Documentation](https://ollama.ai/)