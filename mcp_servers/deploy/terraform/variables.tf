# General Configuration
variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  type        = string
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24", "10.0.30.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.100.0/24", "10.0.200.0/24", "10.0.300.0/24"]
}

# EKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "eks_public_access_cidrs" {
  description = "CIDR blocks for EKS public access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge"]
}

variable "node_capacity_type" {
  description = "Capacity type for EKS nodes (ON_DEMAND or SPOT)"
  type        = string
  default     = "ON_DEMAND"
  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_capacity_type)
    error_message = "Node capacity type must be ON_DEMAND or SPOT."
  }
}

variable "node_desired_size" {
  description = "Desired number of nodes"
  type        = number
  default     = 3
}

variable "node_max_size" {
  description = "Maximum number of nodes"
  type        = number
  default     = 10
}

variable "node_min_size" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "node_max_unavailable" {
  description = "Maximum number of nodes unavailable during update"
  type        = number
  default     = 1
}

variable "ec2_ssh_key" {
  description = "EC2 Key Pair name for SSH access"
  type        = string
  default     = ""
}

# Database Configuration
variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_replica_instance_class" {
  description = "RDS replica instance class"
  type        = string
  default     = "db.t3.small"
}

variable "db_allocated_storage" {
  description = "Initial storage allocation for RDS"
  type        = number
  default     = 100
}

variable "db_max_allocated_storage" {
  description = "Maximum storage allocation for RDS"
  type        = number
  default     = 1000
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "mcpuser"
}

variable "db_backup_retention_period" {
  description = "Database backup retention period in days"
  type        = number
  default     = 7
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in Redis cluster"
  type        = number
  default     = 2
}

variable "redis_snapshot_retention_limit" {
  description = "Redis snapshot retention limit in days"
  type        = number
  default     = 7
}

# Monitoring & Logging
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "alert_email_addresses" {
  description = "Email addresses for alerts"
  type        = list(string)
  default     = []
}

# Domain & SSL
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "mcp-manager.com"
}

variable "manage_dns" {
  description = "Whether to manage DNS with Route53"
  type        = bool
  default     = false
}

# Environment-specific defaults
locals {
  environment_configs = {
    dev = {
      node_desired_size             = 1
      node_max_size                = 3
      node_min_size                = 1
      db_instance_class            = "db.t3.micro"
      db_backup_retention_period   = 1
      redis_node_type              = "cache.t3.micro"
      redis_num_cache_nodes        = 1
      log_retention_days           = 7
    }
    staging = {
      node_desired_size             = 2
      node_max_size                = 5
      node_min_size                = 1
      db_instance_class            = "db.t3.small"
      db_backup_retention_period   = 3
      redis_node_type              = "cache.t3.small"
      redis_num_cache_nodes        = 1
      log_retention_days           = 14
    }
    production = {
      node_desired_size             = 3
      node_max_size                = 20
      node_min_size                = 3
      db_instance_class            = "db.r6g.large"
      db_backup_retention_period   = 30
      redis_node_type              = "cache.r6g.large"
      redis_num_cache_nodes        = 3
      log_retention_days           = 90
    }
  }

  # Merge environment-specific config with variables
  config = merge(
    local.environment_configs[var.environment],
    {
      # Override with any explicitly set variables
      node_desired_size             = var.node_desired_size
      node_max_size                = var.node_max_size
      node_min_size                = var.node_min_size
      db_instance_class            = var.db_instance_class
      db_backup_retention_period   = var.db_backup_retention_period
      redis_node_type              = var.redis_node_type
      redis_num_cache_nodes        = var.redis_num_cache_nodes
      log_retention_days           = var.log_retention_days
    }
  )
}

# OpenSearch Configuration
variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 3
}

variable "opensearch_master_instance_type" {
  description = "OpenSearch dedicated master instance type"
  type        = string
  default     = "t3.small.search"
}

variable "opensearch_ebs_volume_size" {
  description = "EBS volume size for OpenSearch (GB)"
  type        = number
  default     = 20
}

variable "opensearch_master_user" {
  description = "OpenSearch master username"
  type        = string
  default     = "admin"
}

# Tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "MCP-UI"
    ManagedBy = "Terraform"
  }
}