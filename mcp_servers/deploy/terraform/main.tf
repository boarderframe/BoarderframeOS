terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }

  backend "s3" {
    bucket  = var.terraform_state_bucket
    key     = "mcp-ui/terraform.tfstate"
    region  = var.aws_region
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "MCP-UI"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "DevOps"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Random password generation
resource "random_password" "database_password" {
  length  = 32
  special = true
}

resource "random_password" "redis_password" {
  length  = 32
  special = false
}

# VPC Configuration
resource "aws_vpc" "mcp_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "mcp-ui-vpc-${var.environment}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "mcp_igw" {
  vpc_id = aws_vpc.mcp_vpc.id

  tags = {
    Name = "mcp-ui-igw-${var.environment}"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.mcp_vpc.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                     = "mcp-ui-public-subnet-${count.index + 1}-${var.environment}"
    "kubernetes.io/role/elb" = "1"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.mcp_vpc.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name                              = "mcp-ui-private-subnet-${count.index + 1}-${var.environment}"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# Database Subnets
resource "aws_subnet" "database" {
  count = length(var.database_subnet_cidrs)

  vpc_id            = aws_vpc.mcp_vpc.id
  cidr_block        = var.database_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "mcp-ui-database-subnet-${count.index + 1}-${var.environment}"
  }
}

# NAT Gateways
resource "aws_eip" "nat" {
  count = length(aws_subnet.public)

  domain = "vpc"
  depends_on = [aws_internet_gateway.mcp_igw]

  tags = {
    Name = "mcp-ui-nat-eip-${count.index + 1}-${var.environment}"
  }
}

resource "aws_nat_gateway" "mcp_nat" {
  count = length(aws_subnet.public)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "mcp-ui-nat-gateway-${count.index + 1}-${var.environment}"
  }

  depends_on = [aws_internet_gateway.mcp_igw]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.mcp_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.mcp_igw.id
  }

  tags = {
    Name = "mcp-ui-public-rt-${var.environment}"
  }
}

resource "aws_route_table" "private" {
  count = length(aws_nat_gateway.mcp_nat)

  vpc_id = aws_vpc.mcp_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.mcp_nat[count.index].id
  }

  tags = {
    Name = "mcp-ui-private-rt-${count.index + 1}-${var.environment}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Groups
resource "aws_security_group" "eks_cluster" {
  name_prefix = "mcp-ui-eks-cluster-"
  vpc_id      = aws_vpc.mcp_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mcp-ui-eks-cluster-sg-${var.environment}"
  }
}

resource "aws_security_group" "eks_nodes" {
  name_prefix = "mcp-ui-eks-nodes-"
  vpc_id      = aws_vpc.mcp_vpc.id

  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mcp-ui-eks-nodes-sg-${var.environment}"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "mcp-ui-rds-"
  vpc_id      = aws_vpc.mcp_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  tags = {
    Name = "mcp-ui-rds-sg-${var.environment}"
  }
}

resource "aws_security_group" "elasticache" {
  name_prefix = "mcp-ui-elasticache-"
  vpc_id      = aws_vpc.mcp_vpc.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  tags = {
    Name = "mcp-ui-elasticache-sg-${var.environment}"
  }
}

# EKS Cluster
resource "aws_eks_cluster" "mcp_cluster" {
  name     = "mcp-ui-${var.environment}"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    security_group_ids      = [aws_security_group.eks_cluster.id]
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = var.eks_public_access_cidrs
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
  ]

  tags = {
    Name = "mcp-ui-eks-${var.environment}"
  }
}

# EKS Node Groups
resource "aws_eks_node_group" "mcp_nodes" {
  cluster_name    = aws_eks_cluster.mcp_cluster.name
  node_group_name = "mcp-ui-nodes-${var.environment}"
  node_role_arn   = aws_iam_role.eks_node_group.arn
  subnet_ids      = aws_subnet.private[*].id
  instance_types  = var.node_instance_types
  capacity_type   = var.node_capacity_type
  ami_type        = "AL2_x86_64"

  scaling_config {
    desired_size = var.node_desired_size
    max_size     = var.node_max_size
    min_size     = var.node_min_size
  }

  update_config {
    max_unavailable = var.node_max_unavailable
  }

  remote_access {
    ec2_ssh_key               = var.ec2_ssh_key
    source_security_group_ids = [aws_security_group.eks_nodes.id]
  }

  labels = {
    Environment = var.environment
    NodeGroup   = "mcp-ui-nodes"
  }

  taint {
    key    = "app"
    value  = "mcp-ui"
    effect = "NO_SCHEDULE"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]

  tags = {
    Name = "mcp-ui-node-group-${var.environment}"
  }
}

# RDS PostgreSQL
resource "aws_db_subnet_group" "mcp_db" {
  name       = "mcp-ui-db-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.database[*].id

  tags = {
    Name = "mcp-ui-db-subnet-group-${var.environment}"
  }
}

resource "aws_db_instance" "mcp_postgres" {
  allocated_storage                   = var.db_allocated_storage
  max_allocated_storage              = var.db_max_allocated_storage
  storage_type                       = "gp3"
  storage_encrypted                  = true
  kms_key_id                         = aws_kms_key.rds.arn
  engine                             = "postgres"
  engine_version                     = var.postgres_version
  instance_class                     = var.db_instance_class
  identifier                         = "mcp-ui-postgres-${var.environment}"
  db_name                            = "mcpdb"
  username                           = var.db_username
  password                           = random_password.database_password.result
  vpc_security_group_ids             = [aws_security_group.rds.id]
  db_subnet_group_name               = aws_db_subnet_group.mcp_db.name
  backup_retention_period            = var.db_backup_retention_period
  backup_window                      = "03:00-04:00"
  maintenance_window                 = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade         = true
  performance_insights_enabled       = true
  performance_insights_kms_key_id    = aws_kms_key.rds.arn
  monitoring_interval                = 60
  monitoring_role_arn                = aws_iam_role.rds_monitoring.arn
  enabled_cloudwatch_logs_exports    = ["postgresql"]
  deletion_protection                = var.environment == "production"
  skip_final_snapshot                = var.environment != "production"
  final_snapshot_identifier          = var.environment == "production" ? "mcp-ui-postgres-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  apply_immediately                  = var.environment != "production"

  tags = {
    Name = "mcp-ui-postgres-${var.environment}"
  }
}

# Read Replica (Production only)
resource "aws_db_instance" "mcp_postgres_replica" {
  count = var.environment == "production" ? 1 : 0

  identifier                  = "mcp-ui-postgres-replica-${var.environment}"
  replicate_source_db         = aws_db_instance.mcp_postgres.identifier
  instance_class              = var.db_replica_instance_class
  publicly_accessible         = false
  auto_minor_version_upgrade  = true
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn         = aws_iam_role.rds_monitoring.arn
  skip_final_snapshot         = true

  tags = {
    Name = "mcp-ui-postgres-replica-${var.environment}"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "mcp_redis" {
  name       = "mcp-ui-redis-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "mcp-ui-redis-subnet-group-${var.environment}"
  }
}

resource "aws_elasticache_replication_group" "mcp_redis" {
  replication_group_id         = "mcp-ui-redis-${var.environment}"
  description                  = "Redis cluster for MCP-UI ${var.environment}"
  node_type                    = var.redis_node_type
  port                         = 6379
  parameter_group_name         = aws_elasticache_parameter_group.mcp_redis.name
  num_cache_clusters           = var.redis_num_cache_nodes
  automatic_failover_enabled   = var.redis_num_cache_nodes > 1
  multi_az_enabled            = var.redis_num_cache_nodes > 1
  subnet_group_name           = aws_elasticache_subnet_group.mcp_redis.name
  security_group_ids          = [aws_security_group.elasticache.id]
  at_rest_encryption_enabled  = true
  transit_encryption_enabled  = true
  auth_token                  = random_password.redis_password.result
  apply_immediately           = var.environment != "production"
  auto_minor_version_upgrade  = true
  maintenance_window          = "sun:05:00-sun:06:00"
  snapshot_retention_limit    = var.redis_snapshot_retention_limit
  snapshot_window             = "03:00-05:00"
  notification_topic_arn      = aws_sns_topic.alerts.arn

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "slow-log"
  }

  tags = {
    Name = "mcp-ui-redis-${var.environment}"
  }
}

resource "aws_elasticache_parameter_group" "mcp_redis" {
  family = "redis7.x"
  name   = "mcp-ui-redis-params-${var.environment}"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "mcp_assets" {
  bucket = "mcp-ui-assets-${var.environment}-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "mcp-ui-assets-${var.environment}"
  }
}

resource "aws_s3_bucket" "mcp_backups" {
  bucket = "mcp-ui-backups-${var.environment}-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "mcp-ui-backups-${var.environment}"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 Bucket Configurations
resource "aws_s3_bucket_versioning" "mcp_assets" {
  bucket = aws_s3_bucket.mcp_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "mcp_backups" {
  bucket = aws_s3_bucket.mcp_backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_encryption" "mcp_assets" {
  bucket = aws_s3_bucket.mcp_assets.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.s3.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

resource "aws_s3_bucket_encryption" "mcp_backups" {
  bucket = aws_s3_bucket.mcp_backups.id

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        kms_master_key_id = aws_kms_key.s3.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/mcp-ui-${var.environment}/cluster"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "mcp-ui-eks-logs-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/mcp-ui/${var.environment}/application"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "mcp-ui-application-logs-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/mcp-ui-${var.environment}/redis-slow"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "mcp-ui-redis-slow-logs-${var.environment}"
  }
}

# SNS Topics for Alerts
resource "aws_sns_topic" "alerts" {
  name         = "mcp-ui-alerts-${var.environment}"
  display_name = "MCP-UI Alerts - ${title(var.environment)}"
  kms_master_key_id = aws_kms_key.sns.arn

  tags = {
    Name = "mcp-ui-alerts-${var.environment}"
  }
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count = length(var.alert_email_addresses)

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_addresses[count.index]
}

# Application Load Balancer
resource "aws_lb" "mcp_alb" {
  name               = "mcp-ui-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "production"
  enable_http2              = true
  drop_invalid_header_fields = true

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.bucket
    prefix  = "alb-access-logs"
    enabled = true
  }

  tags = {
    Name = "mcp-ui-alb-${var.environment}"
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "mcp-ui-alb-"
  vpc_id      = aws_vpc.mcp_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mcp-ui-alb-sg-${var.environment}"
  }
}

resource "aws_s3_bucket" "alb_logs" {
  bucket = "mcp-ui-alb-logs-${var.environment}-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "mcp-ui-alb-logs-${var.environment}"
  }
}

# Route53 Hosted Zone (if managing DNS)
resource "aws_route53_zone" "mcp_domain" {
  count = var.manage_dns ? 1 : 0

  name = var.domain_name

  tags = {
    Name = "mcp-ui-hosted-zone-${var.environment}"
  }
}

# ACM Certificate
resource "aws_acm_certificate" "mcp_cert" {
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "mcp-ui-certificate-${var.environment}"
  }
}

# Secrets Manager
resource "aws_secretsmanager_secret" "database_credentials" {
  name                    = "mcp-ui/${var.environment}/database"
  description             = "Database credentials for MCP-UI ${var.environment}"
  kms_key_id             = aws_kms_key.secrets_manager.arn
  recovery_window_in_days = var.environment == "production" ? 30 : 0

  tags = {
    Name = "mcp-ui-database-credentials-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "database_credentials" {
  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.database_password.result
    engine   = "postgres"
    host     = aws_db_instance.mcp_postgres.endpoint
    port     = aws_db_instance.mcp_postgres.port
    dbname   = aws_db_instance.mcp_postgres.db_name
  })
}

resource "aws_secretsmanager_secret" "redis_credentials" {
  name                    = "mcp-ui/${var.environment}/redis"
  description             = "Redis credentials for MCP-UI ${var.environment}"
  kms_key_id             = aws_kms_key.secrets_manager.arn
  recovery_window_in_days = var.environment == "production" ? 30 : 0

  tags = {
    Name = "mcp-ui-redis-credentials-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "redis_credentials" {
  secret_id = aws_secretsmanager_secret.redis_credentials.id
  secret_string = jsonencode({
    auth_token = random_password.redis_password.result
    host       = aws_elasticache_replication_group.mcp_redis.primary_endpoint_address
    port       = aws_elasticache_replication_group.mcp_redis.port
  })
}