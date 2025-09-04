# Monitoring Infrastructure
resource "aws_eks_addon" "aws_ebs_csi_driver" {
  cluster_name             = aws_eks_cluster.mcp_cluster.name
  addon_name               = "aws-ebs-csi-driver"
  addon_version            = "v1.25.0-eksbuild.1"
  resolve_conflicts        = "OVERWRITE"
  service_account_role_arn = aws_iam_role.ebs_csi_driver.arn

  depends_on = [aws_eks_node_group.mcp_nodes]

  tags = {
    Name = "mcp-ui-ebs-csi-addon-${var.environment}"
  }
}

# EBS CSI Driver IAM Role
resource "aws_iam_role" "ebs_csi_driver" {
  name = "mcp-ui-ebs-csi-driver-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub" = "system:serviceaccount:kube-system:ebs-csi-controller-sa"
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
    Name = "mcp-ui-ebs-csi-driver-${var.environment}"
  }
}

resource "aws_iam_role_policy_attachment" "ebs_csi_driver" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/Amazon_EBS_CSI_DriverPolicy"
  role       = aws_iam_role.ebs_csi_driver.name
}

# Prometheus and Grafana Infrastructure using AWS Managed Services
resource "aws_prometheus_workspace" "mcp_prometheus" {
  alias = "mcp-ui-${var.environment}"

  logging_configuration {
    log_group_arn = aws_cloudwatch_log_group.prometheus.arn
  }

  tags = {
    Name = "mcp-ui-prometheus-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "prometheus" {
  name              = "/aws/prometheus/mcp-ui-${var.environment}"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "mcp-ui-prometheus-logs-${var.environment}"
  }
}

# Grafana Workspace
resource "aws_grafana_workspace" "mcp_grafana" {
  account_access_type      = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type          = "SERVICE_MANAGED"
  role_arn                = aws_iam_role.grafana.arn
  name                    = "mcp-ui-${var.environment}"
  description             = "Grafana workspace for MCP-UI ${var.environment}"
  data_sources            = ["PROMETHEUS", "CLOUDWATCH", "XRAY"]
  
  configuration = jsonencode({
    unifiedAlerting = {
      enabled = true
    }
    alerting = {
      enabled = true
    }
  })

  tags = {
    Name = "mcp-ui-grafana-${var.environment}"
  }
}

# Grafana IAM Role
resource "aws_iam_role" "grafana" {
  name = "mcp-ui-grafana-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "grafana.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "mcp-ui-grafana-role-${var.environment}"
  }
}

resource "aws_iam_role_policy" "grafana" {
  name = "mcp-ui-grafana-policy-${var.environment}"
  role = aws_iam_role.grafana.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aps:ListWorkspaces",
          "aps:DescribeWorkspace",
          "aps:QueryMetrics",
          "aps:GetLabels",
          "aps:GetSeries",
          "aps:GetMetricMetadata"
        ]
        Resource = aws_prometheus_workspace.mcp_prometheus.arn
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:DescribeAlarmsForMetric",
          "cloudwatch:DescribeAlarmHistory",
          "cloudwatch:DescribeAlarms",
          "cloudwatch:ListMetrics",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:GetMetricData"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:StartQuery",
          "logs:StopQuery",
          "logs:GetQueryResults",
          "logs:GetLogRecord"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/mcp-ui/*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:BatchGetTraces",
          "xray:GetServiceGraph",
          "xray:GetTimeSeriesServiceStatistics",
          "xray:GetTraceSummaries",
          "xray:GetTraceGraph"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeRegions"
        ]
        Resource = "*"
      }
    ]
  })
}

# OpenSearch for Logging
resource "aws_opensearch_domain" "mcp_logs" {
  domain_name    = "mcp-ui-logs-${var.environment}"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type            = var.opensearch_instance_type
    instance_count           = var.opensearch_instance_count
    dedicated_master_enabled = var.opensearch_instance_count > 2
    master_instance_type     = var.opensearch_instance_count > 2 ? var.opensearch_master_instance_type : null
    master_instance_count    = var.opensearch_instance_count > 2 ? 3 : null
    zone_awareness_enabled   = var.opensearch_instance_count > 1
    
    dynamic "zone_awareness_config" {
      for_each = var.opensearch_instance_count > 1 ? [1] : []
      content {
        availability_zone_count = min(var.opensearch_instance_count, length(data.aws_availability_zones.available.names))
      }
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = var.opensearch_ebs_volume_size
  }

  vpc_options {
    security_group_ids = [aws_security_group.opensearch.id]
    subnet_ids         = slice(aws_subnet.private[*].id, 0, min(var.opensearch_instance_count, length(aws_subnet.private)))
  }

  encrypt_at_rest {
    enabled    = true
    kms_key_id = aws_kms_key.opensearch.arn
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    anonymous_auth_enabled         = false
    internal_user_database_enabled = true
    master_user_options {
      master_user_name     = var.opensearch_master_user
      master_user_password = random_password.opensearch_master.result
    }
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
    log_type                 = "INDEX_SLOW_LOGS"
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch.arn
    log_type                 = "SEARCH_SLOW_LOGS"
  }

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.opensearch_es_app.arn
    log_type                 = "ES_APPLICATION_LOGS"
  }

  tags = {
    Name = "mcp-ui-opensearch-${var.environment}"
  }

  depends_on = [aws_iam_service_linked_role.opensearch]
}

resource "aws_iam_service_linked_role" "opensearch" {
  aws_service_name = "opensearchserverless.amazonaws.com"
}

resource "aws_kms_key" "opensearch" {
  description             = "OpenSearch encryption key"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  enable_key_rotation     = true

  tags = {
    Name = "mcp-ui-opensearch-key-${var.environment}"
  }
}

resource "aws_kms_alias" "opensearch" {
  name          = "alias/mcp-ui-opensearch-${var.environment}"
  target_key_id = aws_kms_key.opensearch.key_id
}

resource "random_password" "opensearch_master" {
  length  = 32
  special = true
}

resource "aws_security_group" "opensearch" {
  name_prefix = "mcp-ui-opensearch-"
  vpc_id      = aws_vpc.mcp_vpc.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mcp-ui-opensearch-sg-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "opensearch" {
  name              = "/aws/opensearch/domains/mcp-ui-logs-${var.environment}/index-slow"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "mcp-ui-opensearch-index-slow-logs-${var.environment}"
  }
}

resource "aws_cloudwatch_log_group" "opensearch_es_app" {
  name              = "/aws/opensearch/domains/mcp-ui-logs-${var.environment}/application"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "mcp-ui-opensearch-application-logs-${var.environment}"
  }
}

# X-Ray for Distributed Tracing
resource "aws_xray_encryption_config" "mcp_xray" {
  type   = "KMS"
  key_id = aws_kms_key.xray.arn
}

resource "aws_kms_key" "xray" {
  description             = "X-Ray encryption key"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  enable_key_rotation     = true

  tags = {
    Name = "mcp-ui-xray-key-${var.environment}"
  }
}

resource "aws_kms_alias" "xray" {
  name          = "alias/mcp-ui-xray-${var.environment}"
  target_key_id = aws_kms_key.xray.key_id
}

# CloudWatch Alarms for Critical Metrics
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "mcp-ui-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EKS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors EKS node CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_eks_cluster.mcp_cluster.name
  }

  tags = {
    Name = "mcp-ui-high-cpu-alarm-${var.environment}"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "mcp-ui-high-memory-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/EKS"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors EKS node memory utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_eks_cluster.mcp_cluster.name
  }

  tags = {
    Name = "mcp-ui-high-memory-alarm-${var.environment}"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "mcp-ui-rds-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.mcp_postgres.id
  }

  tags = {
    Name = "mcp-ui-rds-cpu-alarm-${var.environment}"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "mcp-ui-rds-high-connections-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS connection count"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.mcp_postgres.id
  }

  tags = {
    Name = "mcp-ui-rds-connections-alarm-${var.environment}"
  }
}

resource "aws_cloudwatch_metric_alarm" "elasticache_cpu" {
  alarm_name          = "mcp-ui-elasticache-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ElastiCache CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.mcp_redis.id
  }

  tags = {
    Name = "mcp-ui-elasticache-cpu-alarm-${var.environment}"
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_target_response_time" {
  alarm_name          = "mcp-ui-alb-high-response-time-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "2"
  alarm_description   = "This metric monitors ALB target response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.mcp_alb.arn_suffix
  }

  tags = {
    Name = "mcp-ui-alb-response-time-alarm-${var.environment}"
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "mcp-ui-alb-high-5xx-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors ALB 5xx errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.mcp_alb.arn_suffix
  }

  tags = {
    Name = "mcp-ui-alb-5xx-errors-alarm-${var.environment}"
  }
}

# Custom CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "mcp_ui" {
  dashboard_name = "MCP-UI-${title(var.environment)}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EKS", "CPUUtilization", "ClusterName", aws_eks_cluster.mcp_cluster.name],
            [".", "MemoryUtilization", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "EKS Cluster Resource Utilization"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.mcp_postgres.id],
            [".", "DatabaseConnections", ".", "."],
            [".", "ReadLatency", ".", "."],
            [".", "WriteLatency", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "RDS Performance Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.mcp_alb.arn_suffix],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", "CacheClusterId", aws_elasticache_replication_group.mcp_redis.id],
            [".", "DatabaseMemoryUsagePercentage", ".", "."],
            [".", "CurrConnections", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ElastiCache Performance"
          period  = 300
        }
      }
    ]
  })
}