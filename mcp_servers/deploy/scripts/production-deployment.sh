#!/bin/bash
# Production Deployment Script for MCP-UI
# This script provides comprehensive deployment automation with safety checks

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-west-2}"
CLUSTER_NAME="mcp-ui-${ENVIRONMENT}"
NAMESPACE="mcp-ui"
MONITORING_NAMESPACE="mcp-ui-monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Deployment failed with exit code $exit_code"
        log_info "Rolling back changes..."
        rollback_deployment
    fi
    exit $exit_code
}

trap cleanup EXIT

# Rollback function
rollback_deployment() {
    log_warning "Initiating rollback procedure..."
    
    # Rollback to previous version
    kubectl rollout undo deployment/mcp-manager -n $NAMESPACE || true
    kubectl rollout undo deployment/mcp-frontend -n $NAMESPACE || true
    
    # Wait for rollback to complete
    kubectl rollout status deployment/mcp-manager -n $NAMESPACE --timeout=300s || true
    kubectl rollout status deployment/mcp-frontend -n $NAMESPACE --timeout=300s || true
    
    log_warning "Rollback completed"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if kubectl is configured
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "kubectl is not configured or cluster is not accessible"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl get nodes >/dev/null 2>&1; then
        log_error "Cannot access cluster nodes"
        exit 1
    fi
    
    # Check namespace exists
    if ! kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
        log_info "Creating namespace $NAMESPACE"
        kubectl create namespace $NAMESPACE
    fi
    
    # Check monitoring namespace exists
    if ! kubectl get namespace $MONITORING_NAMESPACE >/dev/null 2>&1; then
        log_info "Creating namespace $MONITORING_NAMESPACE"
        kubectl create namespace $MONITORING_NAMESPACE
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured"
        exit 1
    fi
    
    # Check required tools
    for tool in kubectl aws helm; do
        if ! command -v $tool >/dev/null 2>&1; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    log_success "Pre-deployment checks passed"
}

# Infrastructure deployment using Terraform
deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd "${PROJECT_ROOT}/deploy/terraform"
    
    # Initialize Terraform
    terraform init -input=false
    
    # Plan deployment
    terraform plan -var="environment=${ENVIRONMENT}" -out=tfplan
    
    # Apply infrastructure changes
    terraform apply -input=false tfplan
    
    log_success "Infrastructure deployment completed"
}

# Deploy secrets and configuration
deploy_secrets() {
    log_info "Deploying secrets and configuration..."
    
    # Apply external secrets operator first
    kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/external-secrets.yaml" || true
    
    # Wait for external secrets operator to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=external-secrets -n external-secrets-system --timeout=300s || true
    
    # Apply secrets configuration
    kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/mcp-autoscaling.yaml"
    
    # Wait for secrets to be created
    log_info "Waiting for secrets to be populated..."
    for i in {1..60}; do
        if kubectl get secret mcp-secrets -n $NAMESPACE >/dev/null 2>&1; then
            log_success "Secrets are ready"
            break
        fi
        sleep 5
    done
    
    log_success "Secrets deployment completed"
}

# Deploy monitoring stack
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    # Apply cert-manager if not exists
    if ! kubectl get namespace cert-manager >/dev/null 2>&1; then
        log_info "Installing cert-manager..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
        kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
    fi
    
    # Apply certificate configuration
    kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/cert-manager.yaml"
    
    # Install Prometheus Operator if not exists
    if ! helm list -n $MONITORING_NAMESPACE | grep -q kube-prometheus-stack; then
        log_info "Installing Prometheus Operator..."
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update
        
        helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
            --namespace $MONITORING_NAMESPACE \
            --create-namespace \
            --values "${PROJECT_ROOT}/deploy/monitoring/prometheus/values.yaml"
    fi
    
    # Apply monitoring configuration
    kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/monitoring-stack.yaml"
    
    log_success "Monitoring stack deployment completed"
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."
    
    # Apply namespace and RBAC
    kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/namespace.yaml"
    
    # Apply configuration
    kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/mcp-autoscaling.yaml"
    
    # Deploy backend
    log_info "Deploying backend..."
    kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/mcp-manager-deployment.yaml"
    
    # Deploy frontend and ingress
    log_info "Deploying frontend and ingress..."
    kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/mcp-ingress.yaml"
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl rollout status deployment/mcp-manager -n $NAMESPACE --timeout=600s
    kubectl rollout status deployment/mcp-frontend -n $NAMESPACE --timeout=600s
    
    log_success "Application deployment completed"
}

# Health checks
run_health_checks() {
    log_info "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    # Wait for pods to be ready
    while [[ $attempt -le $max_attempts ]]; do
        if kubectl get pods -n $NAMESPACE -l app=mcp-manager --field-selector=status.phase=Running | grep -q Running; then
            log_success "Backend pods are running"
            break
        fi
        log_info "Waiting for backend pods... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Backend pods failed to start"
        return 1
    fi
    
    # Test internal health endpoints
    log_info "Testing internal health endpoints..."
    if kubectl exec -n $NAMESPACE deployment/mcp-manager -- curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    if kubectl exec -n $NAMESPACE deployment/mcp-frontend -- curl -f http://localhost:3000/health >/dev/null 2>&1; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        return 1
    fi
    
    # Test external endpoints (if ingress is ready)
    log_info "Testing external endpoints..."
    local external_url="https://mcp-ui.example.com"
    local api_url="https://api.mcp-ui.example.com"
    
    # Wait for ingress to be ready
    sleep 30
    
    if curl -f -s --max-time 30 "${external_url}/health" >/dev/null 2>&1; then
        log_success "External frontend endpoint accessible"
    else
        log_warning "External frontend endpoint not yet accessible (may need DNS propagation)"
    fi
    
    if curl -f -s --max-time 30 "${api_url}/api/v1/health" >/dev/null 2>&1; then
        log_success "External API endpoint accessible"
    else
        log_warning "External API endpoint not yet accessible (may need DNS propagation)"
    fi
    
    log_success "Health checks completed"
}

# Performance baseline tests
run_performance_tests() {
    log_info "Running performance baseline tests..."
    
    # Simple load test using kubectl and curl
    local test_url="http://mcp-manager-service.${NAMESPACE}.svc.cluster.local:8000/api/v1/health"
    
    # Run load test from within cluster
    kubectl run performance-test \
        --image=curlimages/curl:latest \
        --rm -i --restart=Never \
        --namespace=$NAMESPACE \
        -- /bin/sh -c "
            echo 'Starting performance test...'
            start_time=\$(date +%s)
            success_count=0
            total_requests=100
            
            for i in \$(seq 1 \$total_requests); do
                if curl -f -s --max-time 5 '$test_url' >/dev/null 2>&1; then
                    success_count=\$((success_count + 1))
                fi
                sleep 0.1
            done
            
            end_time=\$(date +%s)
            duration=\$((end_time - start_time))
            success_rate=\$((success_count * 100 / total_requests))
            
            echo \"Performance test completed:\"
            echo \"- Total requests: \$total_requests\"
            echo \"- Successful requests: \$success_count\"
            echo \"- Success rate: \$success_rate%\"
            echo \"- Duration: \$duration seconds\"
            
            if [ \$success_rate -lt 95 ]; then
                echo \"ERROR: Success rate below 95%\"
                exit 1
            fi
        "
    
    if [[ $? -eq 0 ]]; then
        log_success "Performance tests passed"
    else
        log_error "Performance tests failed"
        return 1
    fi
}

# Security validation
run_security_checks() {
    log_info "Running security validation..."
    
    # Check pod security contexts
    log_info "Validating pod security contexts..."
    
    local insecure_pods=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].spec.securityContext.runAsRoot}' | grep -c "true" || echo "0")
    if [[ $insecure_pods -gt 0 ]]; then
        log_warning "$insecure_pods pods are running as root"
    else
        log_success "All pods are running with proper security contexts"
    fi
    
    # Check for privileged containers
    local privileged_containers=$(kubectl get pods -n $NAMESPACE -o jsonpath='{.items[*].spec.containers[*].securityContext.privileged}' | grep -c "true" || echo "0")
    if [[ $privileged_containers -gt 0 ]]; then
        log_error "$privileged_containers privileged containers found"
        return 1
    else
        log_success "No privileged containers found"
    fi
    
    # Check network policies
    if kubectl get networkpolicy -n $NAMESPACE >/dev/null 2>&1; then
        log_success "Network policies are configured"
    else
        log_warning "No network policies found"
    fi
    
    log_success "Security checks completed"
}

# Database migration
run_database_migration() {
    log_info "Running database migrations..."
    
    # Run migration job
    kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: migration
        image: ghcr.io/mcp-ui/backend:latest
        command: ["python", "-m", "alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: database-url
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    # Wait for migration to complete
    log_info "Waiting for database migration to complete..."
    kubectl wait --for=condition=complete job -l job-name=database-migration --timeout=300s -n $NAMESPACE
    
    if [[ $? -eq 0 ]]; then
        log_success "Database migration completed"
    else
        log_error "Database migration failed"
        return 1
    fi
}

# Backup current state before deployment
backup_current_state() {
    log_info "Creating backup of current state..."
    
    local backup_dir="/tmp/mcp-ui-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup current deployments
    kubectl get deployment mcp-manager -n $NAMESPACE -o yaml > "$backup_dir/mcp-manager-deployment.yaml" 2>/dev/null || true
    kubectl get deployment mcp-frontend -n $NAMESPACE -o yaml > "$backup_dir/mcp-frontend-deployment.yaml" 2>/dev/null || true
    
    # Backup configmaps
    kubectl get configmap -n $NAMESPACE -o yaml > "$backup_dir/configmaps.yaml" 2>/dev/null || true
    
    log_success "Backup created at $backup_dir"
}

# Display deployment summary
deployment_summary() {
    log_info "Deployment Summary:"
    echo "===================="
    echo "Environment: $ENVIRONMENT"
    echo "Cluster: $CLUSTER_NAME"
    echo "Namespace: $NAMESPACE"
    echo ""
    
    log_info "Pod Status:"
    kubectl get pods -n $NAMESPACE -o wide
    echo ""
    
    log_info "Service Status:"
    kubectl get services -n $NAMESPACE
    echo ""
    
    log_info "Ingress Status:"
    kubectl get ingress -n $NAMESPACE
    echo ""
    
    log_info "Recent Events:"
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    log_info "Starting MCP-UI production deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Cluster: $CLUSTER_NAME"
    
    # Configure kubectl
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
    
    # Run deployment steps
    pre_deployment_checks
    backup_current_state
    deploy_infrastructure
    deploy_secrets
    deploy_monitoring
    run_database_migration
    deploy_application
    run_health_checks
    run_security_checks
    run_performance_tests
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Deployment completed successfully in ${duration} seconds!"
    deployment_summary
    
    log_info "Next steps:"
    echo "1. Monitor application logs: kubectl logs -f deployment/mcp-manager -n $NAMESPACE"
    echo "2. Check monitoring dashboard: https://grafana.mcp-ui.example.com"
    echo "3. Verify external access: https://mcp-ui.example.com"
    echo "4. Review alerts: https://alertmanager.mcp-ui.example.com"
}

# Help function
show_help() {
    cat << EOF
MCP-UI Production Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENVIRONMENT    Set deployment environment (default: production)
    -r, --region REGION             Set AWS region (default: us-west-2)
    -c, --cluster CLUSTER           Set EKS cluster name (default: mcp-ui-ENVIRONMENT)
    -n, --namespace NAMESPACE       Set Kubernetes namespace (default: mcp-ui)
    -h, --help                      Show this help message

Environment Variables:
    ENVIRONMENT                     Deployment environment
    AWS_REGION                      AWS region
    CLUSTER_NAME                    EKS cluster name

Examples:
    $0                              # Deploy to production
    $0 -e staging                   # Deploy to staging
    $0 -r us-east-1 -e production   # Deploy to production in us-east-1

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -c|--cluster)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Update cluster name based on environment if not explicitly set
if [[ "$CLUSTER_NAME" == "mcp-ui-${ENVIRONMENT}" ]]; then
    CLUSTER_NAME="mcp-ui-${ENVIRONMENT}"
fi

# Run main function
main "$@"