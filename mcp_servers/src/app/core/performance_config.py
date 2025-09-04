"""
Performance Configuration for MCP-UI System
Central configuration for all performance optimization features
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class CacheStrategy(Enum):
    """Cache strategy types"""
    CACHE_FIRST = "cache_first"      # Check cache first, fallback to network
    NETWORK_FIRST = "network_first"  # Try network first, fallback to cache
    CACHE_ONLY = "cache_only"        # Only use cache
    NETWORK_ONLY = "network_only"    # Only use network
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"  # Return stale, update in background


@dataclass
class PerformanceConfig:
    """Central performance configuration"""
    
    # Target performance metrics
    target_response_time_ms: int = 200
    target_lcp_ms: int = 2500
    target_fid_ms: int = 100
    target_cls_score: float = 0.1
    
    # Cache configuration
    redis_url: str = "redis://localhost:6379"
    cache_enabled: bool = True
    cache_ttl_short: int = 60        # 1 minute
    cache_ttl_medium: int = 300      # 5 minutes
    cache_ttl_long: int = 3600       # 1 hour
    cache_ttl_static: int = 86400    # 24 hours
    memory_cache_size: int = 500     # Number of items in memory cache
    
    # CDN configuration
    cdn_enabled: bool = True
    cdn_provider: str = "cloudflare"
    cdn_base_url: str = ""
    cdn_api_key: str = ""
    cdn_zone_id: str = ""
    
    # Compression settings
    compression_enabled: bool = True
    compression_threshold: int = 1024  # Compress responses > 1KB
    compression_level: int = 6         # 1-9, higher = better compression
    preferred_compression: str = "brotli"  # brotli, gzip, deflate
    
    # Connection pooling
    max_connections: int = 100
    connection_timeout: int = 5
    keepalive_timeout: int = 60
    max_keepalive_requests: int = 100
    
    # Database optimization
    db_connection_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    enable_read_replicas: bool = True
    
    # API rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    rate_limit_burst: int = 20
    
    # Background jobs
    background_workers: int = 10
    job_queue_size: int = 1000
    job_timeout: int = 300  # 5 minutes
    
    # Frontend optimization
    enable_service_worker: bool = True
    enable_pwa: bool = True
    enable_lazy_loading: bool = True
    enable_code_splitting: bool = True
    enable_resource_hints: bool = True
    critical_css_inline: bool = True
    
    # Image optimization
    auto_optimize_images: bool = True
    image_quality: int = 85
    image_formats: List[str] = field(default_factory=lambda: ["webp", "avif"])
    responsive_sizes: List[int] = field(default_factory=lambda: [320, 640, 768, 1024, 1440, 1920])
    
    # Monitoring
    enable_monitoring: bool = True
    enable_tracing: bool = True
    metrics_retention_days: int = 30
    alert_threshold_response_time_ms: int = 500
    alert_threshold_error_rate: float = 5.0
    
    # A/B testing
    enable_ab_testing: bool = False
    ab_test_cookie_name: str = "mcp_ab_variant"
    ab_test_variants: Dict[str, float] = field(default_factory=lambda: {"control": 0.5, "variant": 0.5})
    
    # Edge computing
    enable_edge_computing: bool = False
    edge_worker_timeout: int = 50  # milliseconds
    
    # Security headers for performance
    enable_hsts: bool = True
    hsts_max_age: int = 31536000  # 1 year
    enable_csp: bool = True
    
    def get_cache_strategy(self, resource_type: str) -> CacheStrategy:
        """Get cache strategy for resource type"""
        strategies = {
            "api": CacheStrategy.NETWORK_FIRST,
            "static": CacheStrategy.CACHE_FIRST,
            "image": CacheStrategy.STALE_WHILE_REVALIDATE,
            "realtime": CacheStrategy.NETWORK_ONLY,
            "offline": CacheStrategy.CACHE_ONLY
        }
        return strategies.get(resource_type, CacheStrategy.NETWORK_FIRST)
        
    def get_cache_ttl(self, resource_type: str) -> int:
        """Get cache TTL for resource type"""
        ttls = {
            "api": self.cache_ttl_medium,
            "static": self.cache_ttl_static,
            "image": self.cache_ttl_long,
            "user": self.cache_ttl_short,
            "config": self.cache_ttl_long
        }
        return ttls.get(resource_type, self.cache_ttl_medium)


@dataclass
class CDNConfig:
    """CDN-specific configuration"""
    
    # Cloudflare settings
    cloudflare_zone_id: str = ""
    cloudflare_api_key: str = ""
    cloudflare_email: str = ""
    cloudflare_workers_enabled: bool = False
    
    # Fastly settings
    fastly_service_id: str = ""
    fastly_api_key: str = ""
    
    # AWS CloudFront settings
    cloudfront_distribution_id: str = ""
    cloudfront_access_key: str = ""
    cloudfront_secret_key: str = ""
    
    # Cache rules
    cache_rules: Dict[str, Dict] = field(default_factory=lambda: {
        "*.html": {"ttl": 300, "browser_ttl": 0},
        "*.css": {"ttl": 86400, "browser_ttl": 86400},
        "*.js": {"ttl": 86400, "browser_ttl": 86400},
        "*.jpg|*.jpeg|*.png|*.gif": {"ttl": 604800, "browser_ttl": 86400},
        "*.woff|*.woff2": {"ttl": 2592000, "browser_ttl": 2592000},
        "/api/*": {"ttl": 0, "browser_ttl": 0}
    })
    
    # Edge locations
    preferred_edge_locations: List[str] = field(default_factory=lambda: [
        "us-east-1", "us-west-1", "eu-west-1", "ap-southeast-1"
    ])


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    
    # Prometheus settings
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    prometheus_path: str = "/metrics"
    
    # Grafana settings
    grafana_enabled: bool = False
    grafana_url: str = "http://localhost:3000"
    grafana_api_key: str = ""
    
    # OpenTelemetry settings
    otlp_endpoint: str = "http://localhost:4317"
    otlp_enabled: bool = False
    
    # Alerting
    alert_channels: List[str] = field(default_factory=lambda: ["email", "slack"])
    alert_email_recipients: List[str] = field(default_factory=list)
    alert_slack_webhook: str = ""
    
    # Custom metrics
    custom_metrics: Dict[str, Dict] = field(default_factory=lambda: {
        "kroger_api_latency": {"type": "histogram", "buckets": [0.1, 0.5, 1.0, 2.0, 5.0]},
        "mcp_server_health": {"type": "gauge"},
        "cache_efficiency": {"type": "summary"}
    })


@dataclass
class LoadTestConfig:
    """Load testing configuration"""
    
    # Test scenarios
    test_scenarios: Dict[str, Dict] = field(default_factory=lambda: {
        "baseline": {
            "users": 10,
            "duration": 300,
            "ramp_up": 30
        },
        "stress": {
            "users": 100,
            "duration": 600,
            "ramp_up": 60
        },
        "spike": {
            "users": 500,
            "duration": 60,
            "ramp_up": 10
        },
        "endurance": {
            "users": 50,
            "duration": 3600,
            "ramp_up": 120
        }
    })
    
    # Test endpoints
    test_endpoints: List[Dict] = field(default_factory=lambda: [
        {"path": "/api/v1/health", "method": "GET", "weight": 0.1},
        {"path": "/api/v1/servers", "method": "GET", "weight": 0.3},
        {"path": "/api/v1/metrics", "method": "GET", "weight": 0.2},
        {"path": "/api/v1/products/search", "method": "GET", "weight": 0.4}
    ])
    
    # Success criteria
    success_criteria: Dict[str, Any] = field(default_factory=lambda: {
        "max_response_time_ms": 1000,
        "max_error_rate": 1.0,
        "min_requests_per_second": 100,
        "percentile_95_ms": 500,
        "percentile_99_ms": 1000
    })


class PerformancePresets:
    """Pre-configured performance settings"""
    
    @staticmethod
    def development() -> PerformanceConfig:
        """Development environment settings"""
        return PerformanceConfig(
            cache_enabled=False,
            cdn_enabled=False,
            compression_enabled=True,
            rate_limit_enabled=False,
            enable_monitoring=True,
            enable_service_worker=False,
            target_response_time_ms=500
        )
        
    @staticmethod
    def production() -> PerformanceConfig:
        """Production environment settings"""
        return PerformanceConfig(
            cache_enabled=True,
            cdn_enabled=True,
            compression_enabled=True,
            rate_limit_enabled=True,
            enable_monitoring=True,
            enable_service_worker=True,
            target_response_time_ms=200
        )
        
    @staticmethod
    def high_performance() -> PerformanceConfig:
        """Maximum performance settings"""
        return PerformanceConfig(
            cache_enabled=True,
            cdn_enabled=True,
            compression_enabled=True,
            preferred_compression="brotli",
            rate_limit_enabled=True,
            enable_monitoring=True,
            enable_service_worker=True,
            enable_edge_computing=True,
            memory_cache_size=1000,
            max_connections=200,
            background_workers=20,
            target_response_time_ms=100
        )
        
    @staticmethod
    def low_resource() -> PerformanceConfig:
        """Settings for resource-constrained environments"""
        return PerformanceConfig(
            cache_enabled=True,
            cdn_enabled=False,
            compression_enabled=True,
            compression_level=3,
            rate_limit_enabled=True,
            enable_monitoring=False,
            memory_cache_size=100,
            max_connections=50,
            background_workers=5,
            db_connection_pool_size=10,
            target_response_time_ms=500
        )


# Global configuration instance
_performance_config: Optional[PerformanceConfig] = None


def get_performance_config() -> PerformanceConfig:
    """Get global performance configuration"""
    global _performance_config
    
    if _performance_config is None:
        # Default to production settings
        _performance_config = PerformancePresets.production()
        
    return _performance_config


def set_performance_config(config: PerformanceConfig):
    """Set global performance configuration"""
    global _performance_config
    _performance_config = config


def load_performance_config(config_path: str) -> PerformanceConfig:
    """Load performance configuration from file"""
    import json
    from pathlib import Path
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_file, 'r') as f:
        config_data = json.load(f)
        
    config = PerformanceConfig(**config_data)
    set_performance_config(config)
    
    return config