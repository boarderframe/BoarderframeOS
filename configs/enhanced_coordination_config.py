"""
Enhanced Agent Coordination Configuration
Configuration settings for the enhanced message bus and coordination features
"""

# Enhanced Message Bus Configuration
ENHANCED_MESSAGE_BUS_CONFIG = {
    # Database configuration for message persistence
    "database": {
        "path": "data/enhanced_message_bus.db",
        "enable_persistence": True,
        "cleanup_interval_hours": 24,
        "max_message_age_days": 30
    },

    # Routing configuration
    "routing": {
        "default_strategy": "capability_based",
        "enable_load_balancing": True,
        "circuit_breaker_threshold": 5,
        "circuit_breaker_timeout": 60,
        "max_retries": 3,
        "retry_delay_seconds": 1
    },

    # Performance monitoring
    "monitoring": {
        "enable_metrics": True,
        "metrics_collection_interval": 30,
        "performance_tracking": True,
        "delivery_tracking": True
    },

    # Agent discovery
    "discovery": {
        "capability_cache_timeout": 300,  # 5 minutes
        "health_check_interval": 60,     # 1 minute
        "auto_discovery": True
    }
}

# Agent Coordination Manager Configuration
COORDINATION_MANAGER_CONFIG = {
    # Workflow configuration
    "workflows": {
        "max_concurrent_workflows": 50,
        "default_timeout_minutes": 30,
        "step_timeout_minutes": 10,
        "enable_workflow_persistence": True
    },

    # Consensus configuration
    "consensus": {
        "default_voting_method": "majority",
        "voting_timeout_seconds": 300,  # 5 minutes
        "min_participants": 2,
        "max_participants": 20,
        "enable_anonymous_voting": False
    },

    # Auction configuration
    "auctions": {
        "default_duration_seconds": 120,  # 2 minutes
        "min_bid_interval_seconds": 5,
        "max_concurrent_auctions": 10,
        "enable_sealed_bids": True,
        "auto_award": True
    },

    # Coordination patterns
    "patterns": {
        "sequential": {
            "max_steps": 20,
            "allow_step_skipping": False,
            "enable_rollback": True
        },
        "parallel": {
            "max_concurrent_tasks": 10,
            "partial_completion_threshold": 0.8  # 80% completion
        },
        "pipeline": {
            "max_pipeline_depth": 10,
            "buffer_size": 5,
            "enable_backpressure": True
        },
        "scatter_gather": {
            "min_responses": 1,
            "response_timeout_seconds": 120
        }
    }
}

# Agent Controller Configuration
AGENT_CONTROLLER_CONFIG = {
    # Task management
    "tasks": {
        "max_concurrent_tasks_per_agent": 5,
        "default_task_timeout_hours": 1,
        "task_retry_attempts": 3,
        "enable_task_prioritization": True
    },

    # Agent management
    "agents": {
        "restart_cooldown_seconds": 60,
        "health_check_interval_seconds": 120,
        "max_restart_attempts": 3,
        "graceful_shutdown_timeout": 30
    },

    # Coordination features
    "coordination": {
        "enable_enhanced_routing": True,
        "enable_workflow_management": True,
        "enable_consensus_decisions": True,
        "enable_task_auctions": True,
        "capability_discovery_enabled": True
    },

    # Resource limits
    "resources": {
        "max_memory_mb": 1024,
        "max_cpu_percent": 80,
        "max_disk_mb": 512,
        "enforce_limits": True
    }
}

# Agent Capability Definitions
STANDARD_AGENT_CAPABILITIES = {
    # Core capabilities
    "thinking": {
        "name": "thinking",
        "description": "General reasoning and problem-solving",
        "category": "cognitive",
        "complexity": "medium"
    },
    "analysis": {
        "name": "analysis",
        "description": "Data analysis and interpretation",
        "category": "analytical",
        "complexity": "high"
    },
    "research": {
        "name": "research",
        "description": "Information gathering and research",
        "category": "information",
        "complexity": "medium"
    },
    "communication": {
        "name": "communication",
        "description": "Inter-agent and human communication",
        "category": "social",
        "complexity": "low"
    },

    # Specialized capabilities
    "strategic_planning": {
        "name": "strategic_planning",
        "description": "Long-term strategic planning and vision",
        "category": "strategic",
        "complexity": "very_high"
    },
    "data_visualization": {
        "name": "data_visualization",
        "description": "Creating visual representations of data",
        "category": "analytical",
        "complexity": "medium"
    },
    "code_generation": {
        "name": "code_generation",
        "description": "Generating and optimizing code",
        "category": "technical",
        "complexity": "high"
    },
    "decision_making": {
        "name": "decision_making",
        "description": "Making complex decisions with multiple factors",
        "category": "cognitive",
        "complexity": "high"
    },

    # Domain-specific capabilities
    "financial_analysis": {
        "name": "financial_analysis",
        "description": "Financial data analysis and modeling",
        "category": "domain",
        "complexity": "high"
    },
    "market_research": {
        "name": "market_research",
        "description": "Market analysis and competitive intelligence",
        "category": "domain",
        "complexity": "medium"
    },
    "project_management": {
        "name": "project_management",
        "description": "Planning and managing projects",
        "category": "management",
        "complexity": "medium"
    },
    "risk_assessment": {
        "name": "risk_assessment",
        "description": "Identifying and evaluating risks",
        "category": "analytical",
        "complexity": "high"
    }
}

# Coordination Pattern Templates
COORDINATION_TEMPLATES = {
    "simple_sequential": {
        "name": "Simple Sequential",
        "description": "Basic sequential task execution",
        "pattern": "sequential",
        "max_participants": 5,
        "typical_use_cases": ["data_pipeline", "approval_workflow", "step_by_step_analysis"]
    },

    "parallel_analysis": {
        "name": "Parallel Analysis",
        "description": "Multiple agents analyzing different aspects simultaneously",
        "pattern": "parallel",
        "max_participants": 10,
        "typical_use_cases": ["comprehensive_research", "multi_perspective_analysis"]
    },

    "data_pipeline": {
        "name": "Data Processing Pipeline",
        "description": "Sequential data processing with validation stages",
        "pattern": "pipeline",
        "max_participants": 8,
        "typical_use_cases": ["data_transformation", "content_processing", "quality_assurance"]
    },

    "expert_consensus": {
        "name": "Expert Consensus",
        "description": "Gather expert opinions and reach consensus",
        "pattern": "scatter_gather",
        "max_participants": 15,
        "typical_use_cases": ["decision_making", "expert_consultation", "recommendation_systems"]
    },

    "competitive_bidding": {
        "name": "Competitive Task Bidding",
        "description": "Agents compete for task assignments through bidding",
        "pattern": "auction",
        "max_participants": 20,
        "typical_use_cases": ["task_optimization", "resource_allocation", "load_balancing"]
    }
}

# Message Bus Topics and Routing Rules
MESSAGE_ROUTING_CONFIG = {
    # Topic definitions
    "topics": {
        "system_events": {
            "description": "System-wide events and notifications",
            "retention_hours": 24,
            "priority": "high"
        },
        "agent_coordination": {
            "description": "Agent coordination messages",
            "retention_hours": 48,
            "priority": "high"
        },
        "workflow_management": {
            "description": "Workflow execution and management",
            "retention_hours": 72,
            "priority": "medium"
        },
        "task_execution": {
            "description": "Task assignment and execution",
            "retention_hours": 24,
            "priority": "medium"
        },
        "agent_lifecycle": {
            "description": "Agent startup, shutdown, and health",
            "retention_hours": 12,
            "priority": "low"
        }
    },

    # Routing rules
    "routing_rules": {
        "high_priority_direct": {
            "condition": "priority == 'CRITICAL' or priority == 'HIGH'",
            "strategy": "direct",
            "bypass_queue": True
        },
        "capability_based_routing": {
            "condition": "message_type == 'TASK_REQUEST' and required_capabilities is not None",
            "strategy": "capability_based",
            "fallback_strategy": "load_balanced"
        },
        "load_balanced_default": {
            "condition": "to_agent == 'any'",
            "strategy": "load_balanced",
            "exclude_overloaded": True
        },
        "zone_restricted": {
            "condition": "zone_restriction is not None",
            "strategy": "zone_filtered",
            "respect_zone_boundaries": True
        }
    }
}

# Performance and Monitoring Configuration
MONITORING_CONFIG = {
    # Metrics collection
    "metrics": {
        "collection_interval_seconds": 30,
        "retention_days": 7,
        "aggregate_interval_minutes": 5,
        "enable_real_time_monitoring": True
    },

    # Performance thresholds
    "thresholds": {
        "message_delivery_time_ms": 1000,
        "workflow_completion_time_minutes": 30,
        "agent_response_time_ms": 5000,
        "consensus_time_minutes": 5,
        "auction_completion_time_seconds": 120
    },

    # Alerting
    "alerts": {
        "enable_performance_alerts": True,
        "enable_failure_alerts": True,
        "enable_capacity_alerts": True,
        "alert_cooldown_minutes": 15
    },

    # Dashboard
    "dashboard": {
        "enable_web_dashboard": True,
        "update_interval_seconds": 5,
        "show_real_time_metrics": True,
        "show_historical_data": True
    }
}

# Security and Access Control
SECURITY_CONFIG = {
    # Agent authentication
    "authentication": {
        "require_agent_auth": True,
        "auth_token_expiry_hours": 24,
        "enable_mutual_auth": False
    },

    # Message security
    "message_security": {
        "encrypt_sensitive_messages": True,
        "sign_critical_messages": True,
        "validate_message_integrity": True
    },

    # Access control
    "access_control": {
        "enable_capability_based_access": True,
        "restrict_cross_zone_communication": False,
        "audit_message_access": True
    }
}
