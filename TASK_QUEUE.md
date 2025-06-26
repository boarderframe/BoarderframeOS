# Task Queue System

BoarderframeOS uses Celery for distributed task processing.

## Overview

The task queue system enables:
- **Asynchronous Processing**: Offload heavy computations
- **Distributed Execution**: Scale across multiple workers
- **Priority Queues**: Critical tasks get processed first
- **Retry Logic**: Automatic retry with exponential backoff
- **Task Workflows**: Chain, group, and chord patterns
- **Monitoring**: Real-time task status and metrics

## Architecture

### Queues
- **critical**: Urgent system tasks (priority 10)
- **high**: Important agent tasks (priority 5)
- **default**: Normal operations (priority 3)
- **low**: Background tasks (priority 1)
- **agents**: Agent-specific tasks
- **llm**: LLM processing tasks
- **analytics**: Data aggregation tasks

### Workers
Workers can be specialized for different queue types:
```bash
# Start a worker for critical and high priority tasks
./manage_workers.py start --queues critical,high

# Start a worker for agent tasks
./manage_workers.py start --queues agents,llm
```

## Usage

### In Agents

Agents can submit tasks using the BaseAgent methods:

```python
# Submit a task
task_id = await self.submit_task(
    'core.task_queue.agent_think',
    {'context': 'market analysis'},
    priority=TaskPriority.HIGH
)

# Check task status
status = self.get_task_status(task_id)

# Offload heavy computation
result_id = await self.offload_heavy_computation(
    self.complex_analysis,
    data_set
)
```

### Task Examples

See `example_tasks.py` for complete examples:

```python
@app.task(name='agents.solomon.analyze_system')
def solomon_analyze_system(metrics: dict) -> dict:
    # Perform system analysis
    return analysis_result
```

### Workflows

Create complex task workflows:

```python
# Chain: task1 -> task2 -> task3
workflow = chain(
    prepare_data.s(dataset_id),
    process_data.s(),
    generate_report.s()
)

# Group: parallel execution
workflow = group(
    analyze_cpu.s(),
    analyze_memory.s(),
    analyze_network.s()
)

# Chord: parallel -> callback
workflow = chord(
    group([agent_think.s(id) for id in agent_ids]),
    consensus_task.s()
)
```

## Management

### CLI Commands

```bash
# Start workers
./manage_workers.py start
./manage_workers.py cluster --workers 4

# Monitor
./manage_workers.py status
./manage_workers.py monitor

# Submit tasks
./manage_workers.py submit "task_name" '{"arg": "value"}'

# View results
./manage_workers.py result <task_id>
```

### Corporate HQ API

```bash
# Get queue statistics
GET /api/tasks

# Submit a task
POST /api/tasks
{
    "task_name": "agents.solomon.analyze_system",
    "args": [{"cpu": 75}],
    "priority": "high"
}

# Check task status
GET /api/tasks/{task_id}

# Cancel a task
DELETE /api/tasks/{task_id}
```

## Configuration

### Worker Configuration

Edit `core/task_queue.py`:

```python
class CeleryConfig:
    # Worker settings
    worker_prefetch_multiplier = 4
    worker_max_tasks_per_child = 1000
    
    # Task settings
    task_acks_late = True
    task_reject_on_worker_lost = True
```

### Rate Limiting

```python
task_annotations = {
    'core.task_queue.llm_process': {'rate_limit': '10/m'},
    'core.task_queue.analytics_aggregate': {'rate_limit': '100/m'},
}
```

### Periodic Tasks

```python
beat_schedule = {
    'health-check': {
        'task': 'core.task_queue.system_health_check',
        'schedule': timedelta(minutes=5),
    }
}
```

## Monitoring

### Dashboard
View task metrics in Corporate HQ at http://localhost:8888

### Flower (Optional)
```bash
pip install flower
celery -A core.task_queue flower --port=5555
```

Access at http://localhost:5555

### Metrics
- Active tasks per queue
- Task success/failure rates
- Average execution time
- Queue backlogs
- Worker utilization

## Best Practices

1. **Use Appropriate Queues**: Route tasks to correct queues
2. **Set Priorities**: Critical tasks should use HIGH/CRITICAL
3. **Handle Failures**: Implement proper retry logic
4. **Monitor Queues**: Watch for backlogs
5. **Scale Workers**: Add workers for busy queues
6. **Clean Up**: Old task results are auto-cleaned

## Troubleshooting

### Tasks Not Processing
- Check Redis is running: `redis-cli ping`
- Verify workers are running: `./manage_workers.py status`
- Check queue routing in logs

### High Memory Usage
- Reduce `worker_prefetch_multiplier`
- Set `worker_max_tasks_per_child`
- Monitor task result expiration

### Task Failures
- Check worker logs in `logs/celery_worker_*.log`
- Review task retry settings
- Verify task serialization

This distributed task system ensures BoarderframeOS can scale
efficiently while maintaining responsive agent operations.
