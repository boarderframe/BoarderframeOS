"""
Celery Task Queue for BoarderframeOS
Distributed task processing for agents and system operations
"""

from celery import Celery, Task
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun, task_failure, task_success
from kombu import Queue, Exchange
import redis
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# Celery configuration
class CeleryConfig:
    # Broker settings (Redis)
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/1'
    
    # Task settings
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'UTC'
    enable_utc = True
    
    # Task execution settings
    task_acks_late = True
    task_reject_on_worker_lost = True
    task_track_started = True
    task_send_sent_event = True
    
    # Result settings
    result_expires = 3600  # 1 hour
    result_persistent = True
    
    # Worker settings
    worker_prefetch_multiplier = 4
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False
    
    # Queue configuration
    task_default_queue = 'default'
    task_queues = (
        Queue('critical', Exchange('critical'), routing_key='critical', priority=10),
        Queue('high', Exchange('high'), routing_key='high', priority=5),
        Queue('default', Exchange('default'), routing_key='default', priority=3),
        Queue('low', Exchange('low'), routing_key='low', priority=1),
        Queue('agents', Exchange('agents'), routing_key='agents'),
        Queue('llm', Exchange('llm'), routing_key='llm'),
        Queue('analytics', Exchange('analytics'), routing_key='analytics'),
    )
    
    # Routing
    task_routes = {
        'core.task_queue.agent_*': {'queue': 'agents'},
        'core.task_queue.llm_*': {'queue': 'llm'},
        'core.task_queue.analytics_*': {'queue': 'analytics'},
    }
    
    # Rate limiting
    task_annotations = {
        'core.task_queue.llm_process': {'rate_limit': '10/m'},
        'core.task_queue.analytics_aggregate': {'rate_limit': '100/m'},
    }
    
    # Retry settings
    task_default_retry_delay = 60  # 1 minute
    task_max_retries = 3
    
    # Beat schedule (periodic tasks)
    beat_schedule = {
        'health-check': {
            'task': 'core.task_queue.system_health_check',
            'schedule': timedelta(minutes=5),
            'options': {'queue': 'default'}
        },
        'cleanup-old-tasks': {
            'task': 'core.task_queue.cleanup_old_tasks',
            'schedule': timedelta(hours=1),
            'options': {'queue': 'low'}
        },
        'aggregate-metrics': {
            'task': 'core.task_queue.aggregate_metrics',
            'schedule': timedelta(minutes=15),
            'options': {'queue': 'analytics'}
        },
    }


# Create Celery app
app = Celery('boarderframeos')
app.config_from_object(CeleryConfig)


class BoarderframeTask(Task):
    """Base task class with additional features"""
    
    def __init__(self):
        self._redis_client = None
        
    @property
    def redis(self):
        """Get Redis client for task metadata"""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                db=2,
                decode_responses=True
            )
        return self._redis_client
    
    def before_start(self, task_id, args, kwargs):
        """Called before task execution"""
        # Store task metadata
        metadata = {
            'start_time': datetime.utcnow().isoformat(),
            'status': TaskStatus.RUNNING.value,
            'worker': self.request.hostname,
            'args': args,
            'kwargs': kwargs
        }
        self.redis.hset(f"task:{task_id}", mapping=metadata)
        self.redis.expire(f"task:{task_id}", 86400)  # 24 hours
        
    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful task completion"""
        metadata = {
            'end_time': datetime.utcnow().isoformat(),
            'status': TaskStatus.SUCCESS.value,
            'result_size': len(str(retval))
        }
        self.redis.hset(f"task:{task_id}", mapping=metadata)
        
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure"""
        metadata = {
            'end_time': datetime.utcnow().isoformat(),
            'status': TaskStatus.FAILURE.value,
            'error': str(exc),
            'traceback': str(einfo)
        }
        self.redis.hset(f"task:{task_id}", mapping=metadata)
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        retry_count = self.request.retries
        metadata = {
            'status': TaskStatus.RETRY.value,
            'retry_count': retry_count,
            'retry_reason': str(exc)
        }
        self.redis.hset(f"task:{task_id}", mapping=metadata)


# Set base task
app.Task = BoarderframeTask


# Core Tasks
@app.task(name='core.task_queue.agent_think')
def agent_think(agent_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Agent thinking task"""
    logger.info(f"Agent {agent_id} thinking with context: {context}")
    
    # Simulate agent thinking
    import time
    time.sleep(2)
    
    thought = {
        'agent_id': agent_id,
        'thought': f"Processed context with {len(context)} items",
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return thought


@app.task(name='core.task_queue.agent_act', bind=True)
def agent_act(self, agent_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
    """Agent action execution task"""
    logger.info(f"Agent {agent_id} executing action: {action}")
    
    try:
        # Simulate action execution
        import time
        import random
        
        time.sleep(random.uniform(1, 3))
        
        # Random failure for testing retry
        if random.random() < 0.1:
            raise Exception("Simulated action failure")
        
        result = {
            'agent_id': agent_id,
            'action': action['type'],
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as exc:
        logger.error(f"Action failed for agent {agent_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(name='core.task_queue.llm_process')
def llm_process(prompt: str, model: str, agent_id: str) -> Dict[str, Any]:
    """Process LLM request"""
    logger.info(f"Processing LLM request for agent {agent_id}")
    
    # This would integrate with actual LLM
    # For now, simulate
    import time
    time.sleep(3)
    
    response = {
        'agent_id': agent_id,
        'model': model,
        'prompt_length': len(prompt),
        'response': f"Simulated response to: {prompt[:50]}...",
        'tokens_used': len(prompt.split()),
        'cost': 0.001 * len(prompt.split())
    }
    
    return response


@app.task(name='core.task_queue.analytics_aggregate')
def analytics_aggregate(metric_type: str, time_range: str) -> Dict[str, Any]:
    """Aggregate analytics data"""
    logger.info(f"Aggregating {metric_type} for {time_range}")
    
    # Simulate analytics aggregation
    import random
    
    metrics = {
        'metric_type': metric_type,
        'time_range': time_range,
        'total_agents': 5,
        'active_agents': random.randint(3, 5),
        'total_tasks': random.randint(100, 500),
        'success_rate': random.uniform(0.85, 0.99),
        'avg_response_time': random.uniform(0.5, 2.0)
    }
    
    return metrics


@app.task(name='core.task_queue.system_health_check')
def system_health_check() -> Dict[str, Any]:
    """Periodic system health check"""
    logger.info("Running system health check")
    
    # Check various system components
    health = {
        'timestamp': datetime.utcnow().isoformat(),
        'redis': check_redis_health(),
        'postgres': check_postgres_health(),
        'agents': check_agents_health(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    # Store health report
    redis_client = redis.Redis(host='localhost', port=6379, db=2)
    redis_client.lpush('health_checks', json.dumps(health))
    redis_client.ltrim('health_checks', 0, 100)  # Keep last 100 checks
    
    return health


@app.task(name='core.task_queue.cleanup_old_tasks')
def cleanup_old_tasks() -> Dict[str, Any]:
    """Clean up old task metadata"""
    logger.info("Cleaning up old tasks")
    
    redis_client = redis.Redis(host='localhost', port=6379, db=2)
    
    # Find and delete old task keys
    deleted = 0
    for key in redis_client.scan_iter("task:*"):
        task_data = redis_client.hgetall(key)
        if task_data and 'start_time' in task_data:
            start_time = datetime.fromisoformat(task_data['start_time'])
            if datetime.utcnow() - start_time > timedelta(days=7):
                redis_client.delete(key)
                deleted += 1
    
    logger.info(f"Deleted {deleted} old task records")
    
    return {'deleted': deleted, 'timestamp': datetime.utcnow().isoformat()}


# Task chains and workflows
@app.task(name='core.task_queue.agent_workflow')
def agent_workflow(agent_id: str, workflow_type: str) -> Dict[str, Any]:
    """Execute a complete agent workflow"""
    from celery import chain, group, chord
    
    if workflow_type == 'think_act':
        # Chain: think -> act
        workflow = chain(
            agent_think.s(agent_id, {'type': 'analysis'}),
            agent_act.s(agent_id, {'type': 'execute'})
        )
    elif workflow_type == 'parallel_analysis':
        # Group: multiple analyses in parallel
        workflow = group(
            agent_think.s(agent_id, {'type': 'market_analysis'}),
            agent_think.s(agent_id, {'type': 'risk_analysis'}),
            agent_think.s(agent_id, {'type': 'opportunity_analysis'})
        )
    elif workflow_type == 'consensus':
        # Chord: multiple agents -> consensus
        workflow = chord(
            group(
                agent_think.s(f"agent-{i}", {'type': 'proposal'})
                for i in range(3)
            ),
            consensus_task.s()
        )
    else:
        return {'error': f'Unknown workflow type: {workflow_type}'}
    
    result = workflow.apply_async()
    
    return {
        'workflow_id': result.id,
        'workflow_type': workflow_type,
        'agent_id': agent_id,
        'status': 'started'
    }


@app.task(name='core.task_queue.consensus_task')
def consensus_task(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Reach consensus from multiple agent results"""
    logger.info(f"Reaching consensus from {len(results)} results")
    
    # Simple consensus logic
    consensus = {
        'participants': len(results),
        'consensus': 'majority agrees on action',
        'confidence': 0.85,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return consensus


# Helper functions
def check_redis_health() -> Dict[str, Any]:
    """Check Redis health"""
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        info = r.info()
        return {
            'status': 'healthy',
            'version': info.get('redis_version'),
            'connected_clients': info.get('connected_clients'),
            'used_memory': info.get('used_memory_human')
        }
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def check_postgres_health() -> Dict[str, Any]:
    """Check PostgreSQL health"""
    # This would check actual PostgreSQL
    # For now, simulate
    return {
        'status': 'healthy',
        'connections': 45,
        'active_queries': 3
    }


def check_agents_health() -> Dict[str, Any]:
    """Check agents health"""
    # This would check actual agents
    # For now, simulate
    return {
        'total': 5,
        'healthy': 4,
        'warning': 1,
        'critical': 0
    }


def check_disk_space() -> Dict[str, Any]:
    """Check disk space"""
    import shutil
    
    total, used, free = shutil.disk_usage("/")
    return {
        'total_gb': total // (2**30),
        'used_gb': used // (2**30),
        'free_gb': free // (2**30),
        'percent_used': (used / total) * 100
    }


def check_memory_usage() -> Dict[str, Any]:
    """Check memory usage"""
    import psutil
    
    memory = psutil.virtual_memory()
    return {
        'total_gb': memory.total // (2**30),
        'used_gb': memory.used // (2**30),
        'available_gb': memory.available // (2**30),
        'percent_used': memory.percent
    }


# Task management functions
class TaskManager:
    """Manager for Celery tasks"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            db=2,
            decode_responses=True
        )
    
    def submit_task(self, task_name: str, *args, 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   **kwargs) -> str:
        """Submit a task to the queue"""
        # Map priority to queue
        queue_map = {
            TaskPriority.CRITICAL: 'critical',
            TaskPriority.HIGH: 'high',
            TaskPriority.NORMAL: 'default',
            TaskPriority.LOW: 'low',
            TaskPriority.BACKGROUND: 'low'
        }
        
        queue = queue_map.get(priority, 'default')
        
        # Get task function
        task = app.tasks.get(task_name)
        if not task:
            raise ValueError(f"Unknown task: {task_name}")
        
        # Submit task
        result = task.apply_async(args=args, kwargs=kwargs, queue=queue)
        
        # Store submission metadata
        metadata = {
            'task_name': task_name,
            'priority': priority.value,
            'queue': queue,
            'submitted_at': datetime.utcnow().isoformat()
        }
        self.redis_client.hset(f"task:{result.id}", mapping=metadata)
        
        return result.id
    
    def get_task_status(self, task_id: str) -> TaskResult:
        """Get status of a task"""
        result = AsyncResult(task_id, app=app)
        
        # Get metadata from Redis
        metadata = self.redis_client.hgetall(f"task:{task_id}")
        
        # Build task result
        task_result = TaskResult(
            task_id=task_id,
            status=self._map_celery_state(result.state),
            result=result.result if result.successful() else None,
            error=str(result.info) if result.failed() else None,
            metadata=metadata
        )
        
        if metadata.get('start_time'):
            task_result.start_time = datetime.fromisoformat(metadata['start_time'])
        
        if metadata.get('end_time'):
            task_result.end_time = datetime.fromisoformat(metadata['end_time'])
            if task_result.start_time:
                task_result.duration = (
                    task_result.end_time - task_result.start_time
                ).total_seconds()
        
        return task_result
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        result = AsyncResult(task_id, app=app)
        result.revoke(terminate=True)
        
        # Update metadata
        self.redis_client.hset(f"task:{task_id}", 'status', TaskStatus.CANCELLED.value)
        
        return True
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {}
        
        # Get queue lengths
        inspect = app.control.inspect()
        
        if inspect:
            active = inspect.active()
            scheduled = inspect.scheduled()
            reserved = inspect.reserved()
            
            stats['active'] = sum(len(tasks) for tasks in (active or {}).values())
            stats['scheduled'] = sum(len(tasks) for tasks in (scheduled or {}).values())
            stats['reserved'] = sum(len(tasks) for tasks in (reserved or {}).values())
        
        # Get Redis queue lengths
        for queue_name in ['critical', 'high', 'default', 'low', 'agents', 'llm', 'analytics']:
            queue_key = f"celery:queue:{queue_name}"
            stats[f'queue_{queue_name}'] = self.redis_client.llen(queue_key)
        
        return stats
    
    def _map_celery_state(self, state: str) -> TaskStatus:
        """Map Celery state to TaskStatus"""
        mapping = {
            'PENDING': TaskStatus.PENDING,
            'STARTED': TaskStatus.RUNNING,
            'SUCCESS': TaskStatus.SUCCESS,
            'FAILURE': TaskStatus.FAILURE,
            'RETRY': TaskStatus.RETRY,
            'REVOKED': TaskStatus.CANCELLED
        }
        return mapping.get(state, TaskStatus.PENDING)


# Async wrapper for Celery tasks
def async_task(task_func):
    """Decorator to make Celery tasks work with asyncio"""
    @wraps(task_func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            task_func.apply_async, 
            args, 
            kwargs
        )
        return result
    return wrapper


# Global task manager instance
_task_manager = None


def get_task_manager() -> TaskManager:
    """Get the global task manager instance"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager