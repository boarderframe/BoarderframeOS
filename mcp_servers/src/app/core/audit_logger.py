"""
Comprehensive Audit Logging System for MCP-UI
GDPR/CCPA Compliant with Advanced Analytics and Retention
"""

import os
import json
import uuid
import hashlib
import gzip
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta, timezone
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
from pathlib import Path
import csv
import io

import redis
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Integer, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import pandas as pd

# ============================================================================
# AUDIT EVENT TYPES
# ============================================================================

class AuditEventType(str, Enum):
    """Comprehensive audit event categorization"""
    
    # Authentication Events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_TOKEN_REVOKE = "auth.token.revoke"
    AUTH_MFA_ENABLED = "auth.mfa.enabled"
    AUTH_MFA_DISABLED = "auth.mfa.disabled"
    AUTH_MFA_VERIFIED = "auth.mfa.verified"
    AUTH_PASSWORD_CHANGED = "auth.password.changed"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    
    # Authorization Events
    AUTHZ_ACCESS_GRANTED = "authz.access.granted"
    AUTHZ_ACCESS_DENIED = "authz.access.denied"
    AUTHZ_ROLE_ASSIGNED = "authz.role.assigned"
    AUTHZ_ROLE_REVOKED = "authz.role.revoked"
    AUTHZ_PERMISSION_GRANTED = "authz.permission.granted"
    AUTHZ_PERMISSION_REVOKED = "authz.permission.revoked"
    
    # Data Events
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    DATA_ENCRYPT = "data.encrypt"
    DATA_DECRYPT = "data.decrypt"
    
    # Configuration Events
    CONFIG_CHANGED = "config.changed"
    CONFIG_EXPORTED = "config.exported"
    CONFIG_IMPORTED = "config.imported"
    CONFIG_VALIDATED = "config.validated"
    
    # Security Events
    SECURITY_THREAT_DETECTED = "security.threat.detected"
    SECURITY_VULNERABILITY_FOUND = "security.vulnerability.found"
    SECURITY_ATTACK_BLOCKED = "security.attack.blocked"
    SECURITY_SCAN_COMPLETED = "security.scan.completed"
    SECURITY_POLICY_VIOLATION = "security.policy.violation"
    
    # Compliance Events
    COMPLIANCE_GDPR_REQUEST = "compliance.gdpr.request"
    COMPLIANCE_CCPA_REQUEST = "compliance.ccpa.request"
    COMPLIANCE_DATA_RETENTION = "compliance.data.retention"
    COMPLIANCE_DATA_DELETION = "compliance.data.deletion"
    COMPLIANCE_CONSENT_GIVEN = "compliance.consent.given"
    COMPLIANCE_CONSENT_WITHDRAWN = "compliance.consent.withdrawn"
    
    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"
    
    # API Events
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"
    API_RATE_LIMIT = "api.rate_limit"
    
    # MCP Server Events
    MCP_SERVER_STARTED = "mcp.server.started"
    MCP_SERVER_STOPPED = "mcp.server.stopped"
    MCP_SERVER_ERROR = "mcp.server.error"
    MCP_TOOL_EXECUTED = "mcp.tool.executed"
    MCP_RESOURCE_ACCESSED = "mcp.resource.accessed"

class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# ============================================================================
# AUDIT LOG MODEL
# ============================================================================

Base = declarative_base()

class AuditLog(Base):
    """SQLAlchemy model for audit logs"""
    __tablename__ = "audit_logs"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    
    # Actor information
    user_id = Column(String(255), index=True)
    user_email = Column(String(255))
    user_roles = Column(JSON)
    session_id = Column(String(255), index=True)
    
    # Request context
    correlation_id = Column(String(255), index=True)
    request_id = Column(String(255), index=True)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(String(500))
    request_params = Column(JSON)
    
    # Event details
    resource_type = Column(String(100), index=True)
    resource_id = Column(String(255), index=True)
    action = Column(String(100))
    result = Column(String(50))  # success, failure, partial
    error_message = Column(Text)
    
    # Additional data
    metadata = Column(JSON)
    tags = Column(JSON)
    
    # Compliance fields
    data_classification = Column(String(50))  # public, internal, confidential, restricted
    contains_pii = Column(Boolean, default=False)
    compliance_flags = Column(JSON)  # GDPR, CCPA, HIPAA, etc.
    
    # Performance metrics
    duration_ms = Column(Integer)
    
    # Indexing for common queries
    __table_args__ = (
        Index('idx_timestamp_event', 'timestamp', 'event_type'),
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_resource', 'resource_type', 'resource_id'),
        Index('idx_compliance', 'contains_pii', 'data_classification'),
    )

# ============================================================================
# AUDIT EVENT MODEL
# ============================================================================

@dataclass
class AuditEvent:
    """Structured audit event"""
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_roles: Optional[List[str]] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    request_params: Optional[Dict[str, Any]] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    data_classification: Optional[str] = None
    contains_pii: bool = False
    compliance_flags: Optional[List[str]] = None
    duration_ms: Optional[int] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data
    
    def anonymize(self) -> 'AuditEvent':
        """Anonymize PII for compliance"""
        if self.contains_pii:
            self.user_email = self._hash_pii(self.user_email)
            self.ip_address = self._hash_pii(self.ip_address)
            
            # Anonymize metadata fields
            if self.metadata:
                pii_fields = ['email', 'phone', 'ssn', 'address', 'name']
                for field in pii_fields:
                    if field in self.metadata:
                        self.metadata[field] = self._hash_pii(self.metadata[field])
        
        return self
    
    def _hash_pii(self, value: Optional[str]) -> Optional[str]:
        """Hash PII data for anonymization"""
        if not value:
            return value
        return hashlib.sha256(f"{value}:salt".encode()).hexdigest()[:16]

# ============================================================================
# AUDIT LOGGER
# ============================================================================

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        database_url: Optional[str] = None,
        retention_days: int = 2555,  # 7 years default
        enable_compression: bool = True
    ):
        self.redis = redis_client
        self.retention_days = retention_days
        self.enable_compression = enable_compression
        
        # Initialize database if URL provided
        self.db_engine = None
        self.db_session = None
        if database_url:
            self.db_engine = create_engine(database_url)
            Base.metadata.create_all(self.db_engine)
            self.db_session = sessionmaker(bind=self.db_engine)
        
        # Buffer for batch writes
        self.event_buffer: List[AuditEvent] = []
        self.buffer_size = 100
        self.flush_interval = 5  # seconds
        
        # Start background flush task
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for buffer flushing"""
        asyncio.create_task(self._flush_buffer_periodically())
    
    async def _flush_buffer_periodically(self):
        """Periodically flush event buffer"""
        while True:
            await asyncio.sleep(self.flush_interval)
            if self.event_buffer:
                await self.flush_buffer()
    
    async def log_event(self, event: AuditEvent):
        """Log an audit event"""
        # Add to buffer
        self.event_buffer.append(event)
        
        # Store in Redis for real-time access
        await self._store_in_redis(event)
        
        # Flush if buffer is full
        if len(self.event_buffer) >= self.buffer_size:
            await self.flush_buffer()
    
    async def _store_in_redis(self, event: AuditEvent):
        """Store event in Redis for real-time access"""
        event_id = str(uuid.uuid4())
        event_data = event.to_dict()
        
        # Compress if enabled
        if self.enable_compression:
            event_json = json.dumps(event_data)
            event_bytes = gzip.compress(event_json.encode())
            key = f"audit:compressed:{event_id}"
            self.redis.setex(key, 86400, event_bytes)  # 24 hour TTL
        else:
            key = f"audit:{event_id}"
            self.redis.setex(key, 86400, json.dumps(event_data))
        
        # Add to indices
        date_key = event.timestamp.strftime("%Y-%m-%d")
        self.redis.sadd(f"audit:index:date:{date_key}", event_id)
        self.redis.expire(f"audit:index:date:{date_key}", 86400 * 7)
        
        if event.user_id:
            self.redis.sadd(f"audit:index:user:{event.user_id}", event_id)
            self.redis.expire(f"audit:index:user:{event.user_id}", 86400 * 7)
        
        if event.event_type:
            self.redis.sadd(f"audit:index:type:{event.event_type.value}", event_id)
            self.redis.expire(f"audit:index:type:{event.event_type.value}", 86400 * 7)
    
    async def flush_buffer(self):
        """Flush event buffer to persistent storage"""
        if not self.event_buffer:
            return
        
        events_to_flush = self.event_buffer.copy()
        self.event_buffer.clear()
        
        # Store in database if configured
        if self.db_session:
            await self._store_in_database(events_to_flush)
        
        # Store in file for backup
        await self._store_in_file(events_to_flush)
    
    async def _store_in_database(self, events: List[AuditEvent]):
        """Store events in database"""
        session = self.db_session()
        try:
            for event in events:
                log_entry = AuditLog(
                    timestamp=event.timestamp,
                    event_type=event.event_type.value,
                    severity=event.severity.value,
                    user_id=event.user_id,
                    user_email=event.user_email,
                    user_roles=event.user_roles,
                    session_id=event.session_id,
                    correlation_id=event.correlation_id,
                    request_id=event.request_id,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    request_method=event.request_method,
                    request_path=event.request_path,
                    request_params=event.request_params,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    action=event.action,
                    result=event.result,
                    error_message=event.error_message,
                    metadata=event.metadata,
                    tags=event.tags,
                    data_classification=event.data_classification,
                    contains_pii=event.contains_pii,
                    compliance_flags=event.compliance_flags,
                    duration_ms=event.duration_ms
                )
                session.add(log_entry)
            
            session.commit()
        except Exception as e:
            session.rollback()
            # Log error but don't fail
            print(f"Failed to store audit logs in database: {e}")
        finally:
            session.close()
    
    async def _store_in_file(self, events: List[AuditEvent]):
        """Store events in file for backup"""
        # Create audit log directory
        log_dir = Path("/var/log/mcp-ui/audit")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with date
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = log_dir / f"audit-{date_str}.jsonl.gz"
        
        # Write events
        with gzip.open(log_file, 'at') as f:
            for event in events:
                f.write(json.dumps(event.to_dict()) + '\n')
    
    async def query_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit events"""
        if self.db_session:
            return await self._query_from_database(
                start_date, end_date, user_id, event_type,
                severity, resource_type, resource_id, limit, offset
            )
        else:
            return await self._query_from_redis(
                start_date, end_date, user_id, event_type, limit
            )
    
    async def _query_from_database(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        user_id: Optional[str],
        event_type: Optional[AuditEventType],
        severity: Optional[AuditSeverity],
        resource_type: Optional[str],
        resource_id: Optional[str],
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """Query events from database"""
        session = self.db_session()
        try:
            query = session.query(AuditLog)
            
            if start_date:
                query = query.filter(AuditLog.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditLog.timestamp <= end_date)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if event_type:
                query = query.filter(AuditLog.event_type == event_type.value)
            if severity:
                query = query.filter(AuditLog.severity == severity.value)
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            if resource_id:
                query = query.filter(AuditLog.resource_id == resource_id)
            
            query = query.order_by(AuditLog.timestamp.desc())
            query = query.limit(limit).offset(offset)
            
            results = []
            for log in query.all():
                results.append({
                    'id': str(log.id),
                    'timestamp': log.timestamp.isoformat(),
                    'event_type': log.event_type,
                    'severity': log.severity,
                    'user_id': log.user_id,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'action': log.action,
                    'result': log.result,
                    'metadata': log.metadata
                })
            
            return results
            
        finally:
            session.close()
    
    async def _query_from_redis(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        user_id: Optional[str],
        event_type: Optional[AuditEventType],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Query events from Redis"""
        event_ids = set()
        
        # Get event IDs from indices
        if user_id:
            user_events = self.redis.smembers(f"audit:index:user:{user_id}")
            event_ids.update(user_events)
        
        if event_type:
            type_events = self.redis.smembers(f"audit:index:type:{event_type.value}")
            if event_ids:
                event_ids = event_ids.intersection(type_events)
            else:
                event_ids.update(type_events)
        
        # If no specific filters, get recent events
        if not event_ids:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            event_ids = self.redis.smembers(f"audit:index:date:{date_str}")
        
        # Retrieve events
        results = []
        for event_id in list(event_ids)[:limit]:
            event_data = None
            
            # Try compressed first
            compressed_key = f"audit:compressed:{event_id.decode() if isinstance(event_id, bytes) else event_id}"
            compressed_data = self.redis.get(compressed_key)
            
            if compressed_data:
                decompressed = gzip.decompress(compressed_data)
                event_data = json.loads(decompressed)
            else:
                # Try uncompressed
                key = f"audit:{event_id.decode() if isinstance(event_id, bytes) else event_id}"
                data = self.redis.get(key)
                if data:
                    event_data = json.loads(data)
            
            if event_data:
                results.append(event_data)
        
        return results
    
    async def export_audit_logs(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        anonymize: bool = False
    ) -> bytes:
        """Export audit logs for compliance"""
        events = await self.query_events(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if anonymize:
            # Anonymize PII in events
            for event in events:
                if event.get('contains_pii'):
                    event['user_email'] = self._hash_value(event.get('user_email'))
                    event['ip_address'] = self._hash_value(event.get('ip_address'))
        
        if format == "json":
            return json.dumps(events, indent=2).encode()
        elif format == "csv":
            # Convert to CSV
            df = pd.DataFrame(events)
            return df.to_csv(index=False).encode()
        elif format == "jsonl":
            # JSON Lines format
            lines = [json.dumps(event) for event in events]
            return '\n'.join(lines).encode()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _hash_value(self, value: Optional[str]) -> Optional[str]:
        """Hash value for anonymization"""
        if not value:
            return value
        return hashlib.sha256(f"{value}:salt".encode()).hexdigest()[:16]
    
    async def cleanup_old_logs(self):
        """Clean up old audit logs based on retention policy"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        
        if self.db_session:
            session = self.db_session()
            try:
                # Delete old logs from database
                session.query(AuditLog).filter(
                    AuditLog.timestamp < cutoff_date
                ).delete()
                session.commit()
            finally:
                session.close()
        
        # Clean up old files
        log_dir = Path("/var/log/mcp-ui/audit")
        if log_dir.exists():
            for log_file in log_dir.glob("audit-*.jsonl.gz"):
                # Parse date from filename
                file_date_str = log_file.stem.replace("audit-", "")
                try:
                    file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
                    if file_date.replace(tzinfo=timezone.utc) < cutoff_date:
                        log_file.unlink()
                except ValueError:
                    pass  # Skip invalid filenames

# ============================================================================
# AUDIT CONTEXT MANAGER
# ============================================================================

class AuditContext:
    """Context manager for audit logging"""
    
    def __init__(
        self,
        logger: AuditLogger,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        self.logger = logger
        self.event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = datetime.now(timezone.utc)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Calculate duration
        if self.start_time:
            duration = (datetime.now(timezone.utc) - self.start_time).total_seconds() * 1000
            self.event.duration_ms = int(duration)
        
        # Set result based on exception
        if exc_val:
            self.event.result = "failure"
            self.event.error_message = str(exc_val)
            self.event.severity = AuditSeverity.ERROR
        else:
            self.event.result = "success"
        
        # Log the event
        await self.logger.log_event(self.event)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'AuditEventType',
    'AuditSeverity',
    'AuditEvent',
    'AuditLogger',
    'AuditContext',
    'AuditLog'
]