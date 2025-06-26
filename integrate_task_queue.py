#!/usr/bin/env python3
"""
Task Queue Integration Script
Adds Celery task queue support to existing BoarderframeOS components
"""

import os
import sys
import re
from pathlib import Path
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_header():
    """Print script header"""
    print("=" * 60)
    print("BoarderframeOS Task Queue Integration")
    print("=" * 60)
    print("Adding distributed task processing to agents and services")
    print()


def backup_file(file_path: Path) -> Path:
    """Create backup of a file"""
    backup_path = file_path.with_suffix(file_path.suffix + '.taskqueue_backup')
    shutil.copy2(file_path, backup_path)
    return backup_path


def update_base_agent():
    """Add task queue support to BaseAgent"""
    base_agent_file = Path("core/base_agent.py")
    
    if not base_agent_file.exists():
        print("  ⚠️  core/base_agent.py not found")
        return False
    
    try:
        with open(base_agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if already has task queue
        if 'task_queue' in content:
            print("  ℹ️  BaseAgent already has task queue support")
            return False
        
        # Add import
        task_imports = """from core.task_queue import get_task_manager, TaskPriority
from core.agent_health import get_health_monitor"""
        
        # Find where to insert imports
        if "import logging" in content:
            content = content.replace("import logging", f"import logging\n{task_imports}")
        
        # Add task queue methods
        task_methods = '''
    async def submit_task(self, task_name: str, *args, 
                         priority: TaskPriority = TaskPriority.NORMAL,
                         **kwargs) -> str:
        """Submit a task to the distributed queue"""
        task_manager = get_task_manager()
        
        # Add agent context
        kwargs['agent_id'] = f"agent-{self.name.lower().replace(' ', '-')}"
        kwargs['agent_name'] = self.name
        
        task_id = task_manager.submit_task(
            task_name, 
            *args,
            priority=priority,
            **kwargs
        )
        
        logger.info(f"Agent {self.name} submitted task {task_id}: {task_name}")
        return task_id
    
    async def offload_heavy_computation(self, computation_func, *args, **kwargs):
        """Offload heavy computation to task queue"""
        # This would serialize the function and arguments
        # For now, use predefined tasks
        return await self.submit_task(
            'core.task_queue.agent_think',
            f"agent-{self.name.lower().replace(' ', '-')}",
            {'computation': computation_func.__name__, 'args': args},
            priority=TaskPriority.NORMAL
        )
    
    async def schedule_periodic_task(self, task_name: str, interval: int, 
                                   *args, **kwargs):
        """Schedule a periodic task"""
        # This would set up a periodic task
        # Implementation depends on Celery beat configuration
        logger.info(f"Agent {self.name} scheduling periodic task: {task_name}")
        
    def get_task_status(self, task_id: str):
        """Get status of a submitted task"""
        task_manager = get_task_manager()
        return task_manager.get_task_status(task_id)'''
        
        # Find where to add (before the last line of the class)
        class_end = content.rfind('\n\n')
        if class_end > 0:
            content = content[:class_end] + task_methods + content[class_end:]
        
        # Write updated content
        if content != original_content:
            backup_file(base_agent_file)
            with open(base_agent_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated core/base_agent.py with task queue support")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating BaseAgent: {e}")
        return False


def update_corporate_hq():
    """Add task queue endpoints to Corporate HQ"""
    corp_hq_file = Path("corporate_headquarters.py")
    
    if not corp_hq_file.exists():
        print("  ⚠️  corporate_headquarters.py not found")
        return False
    
    try:
        with open(corp_hq_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add task queue endpoints
        if '/api/tasks' not in content:
            task_endpoints = '''
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get task queue statistics"""
    from core.task_queue import get_task_manager
    
    task_manager = get_task_manager()
    stats = task_manager.get_queue_stats()
    
    return jsonify({
        'queue_stats': stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get status of a specific task"""
    from core.task_queue import get_task_manager
    
    task_manager = get_task_manager()
    
    try:
        result = task_manager.get_task_status(task_id)
        return jsonify(result.to_dict() if hasattr(result, 'to_dict') else {
            'task_id': task_id,
            'status': result.status.value,
            'result': result.result,
            'error': result.error
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/tasks', methods=['POST'])
def submit_task():
    """Submit a new task to the queue"""
    from core.task_queue import get_task_manager, TaskPriority
    
    data = request.json
    task_name = data.get('task_name')
    args = data.get('args', [])
    kwargs = data.get('kwargs', {})
    priority = data.get('priority', 'normal')
    
    if not task_name:
        return jsonify({'error': 'task_name required'}), 400
    
    # Map priority
    priority_map = {
        'critical': TaskPriority.CRITICAL,
        'high': TaskPriority.HIGH,
        'normal': TaskPriority.NORMAL,
        'low': TaskPriority.LOW,
        'background': TaskPriority.BACKGROUND
    }
    
    task_manager = get_task_manager()
    
    try:
        task_id = task_manager.submit_task(
            task_name,
            *args,
            priority=priority_map.get(priority, TaskPriority.NORMAL),
            **kwargs
        )
        
        return jsonify({
            'task_id': task_id,
            'status': 'submitted'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """Cancel a task"""
    from core.task_queue import get_task_manager
    
    task_manager = get_task_manager()
    
    try:
        task_manager.cancel_task(task_id)
        return jsonify({'status': 'cancelled'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500'''
            
            # Find where to add (after other API endpoints)
            api_section = content.find("@app.route('/api/")
            if api_section > 0:
                # Find the end of the last route
                next_section = content.find('\n\n\n', api_section)
                if next_section > 0:
                    content = content[:next_section] + '\n' + task_endpoints + content[next_section:]
        
        # Write updated content
        if content != original_content:
            backup_file(corp_hq_file)
            with open(corp_hq_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated corporate_headquarters.py with task queue endpoints")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating Corporate HQ: {e}")
        return False


def update_startup():
    """Add Celery worker startup to startup.py"""
    startup_file = Path("startup.py")
    
    if not startup_file.exists():
        print("  ⚠️  startup.py not found")
        return False
    
    try:
        with open(startup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add Celery worker startup
        if 'celery worker' not in content:
            celery_startup = '''
    # Start Celery workers
    print("Starting Celery task queue workers...")
    celery_process = subprocess.Popen(
        [sys.executable, "manage_workers.py", "cluster", "--workers", "2"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)
    if celery_process.poll() is None:
        print("✓ Celery workers started")
    else:
        print("⚠️  Failed to start Celery workers")
'''
            
            # Find where to add (after other services)
            services_pos = content.find('print("✓ All services started successfully!")')
            if services_pos > 0:
                insert_pos = content.rfind('\n', 0, services_pos)
                content = content[:insert_pos] + celery_startup + content[insert_pos:]
        
        # Write updated content
        if content != original_content:
            backup_file(startup_file)
            with open(startup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated startup.py with Celery worker startup")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating startup: {e}")
        return False


def create_example_tasks():
    """Create example task implementations"""
    example_file = Path("example_tasks.py")
    
    example_content = '''#!/usr/bin/env python3
"""
Example Tasks for BoarderframeOS
Demonstrates how to create and use Celery tasks
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.task_queue import app, BoarderframeTask
from celery import group, chain, chord
import time
import random
from datetime import datetime


# Agent-specific tasks
@app.task(base=BoarderframeTask, name='agents.solomon.analyze_system')
def solomon_analyze_system(metrics: dict) -> dict:
    """Solomon's system analysis task"""
    print(f"Solomon analyzing system metrics: {metrics}")
    
    # Simulate analysis
    time.sleep(random.uniform(2, 5))
    
    analysis = {
        'agent': 'Solomon',
        'timestamp': datetime.utcnow().isoformat(),
        'health_score': random.uniform(0.85, 0.98),
        'recommendations': [
            'Scale agent cluster by 2 nodes',
            'Optimize memory usage in David agent',
            'Review error logs for Adam agent'
        ],
        'priority_actions': []
    }
    
    if metrics.get('error_rate', 0) > 0.1:
        analysis['priority_actions'].append('High error rate detected - immediate action required')
    
    return analysis


@app.task(base=BoarderframeTask, name='agents.david.strategic_planning')
def david_strategic_planning(market_data: dict, agent_performance: dict) -> dict:
    """David's strategic planning task"""
    print(f"David performing strategic planning")
    
    # Simulate planning
    time.sleep(random.uniform(3, 6))
    
    strategy = {
        'agent': 'David',
        'timestamp': datetime.utcnow().isoformat(),
        'revenue_projection': random.uniform(12000, 18000),
        'growth_rate': random.uniform(0.15, 0.25),
        'strategic_initiatives': [
            'Launch premium agent tier',
            'Expand into healthcare vertical',
            'Implement enterprise features'
        ],
        'resource_allocation': {
            'development': 0.40,
            'sales': 0.25,
            'operations': 0.20,
            'research': 0.15
        }
    }
    
    return strategy


@app.task(base=BoarderframeTask, name='agents.adam.generate_agent')
def adam_generate_agent(agent_spec: dict) -> dict:
    """Adam's agent generation task"""
    print(f"Adam generating new agent: {agent_spec}")
    
    # Simulate agent generation
    time.sleep(random.uniform(5, 10))
    
    new_agent = {
        'agent': 'Adam',
        'timestamp': datetime.utcnow().isoformat(),
        'agent_id': f"agent-{agent_spec['name'].lower().replace(' ', '-')}",
        'name': agent_spec['name'],
        'type': agent_spec.get('type', 'worker'),
        'department': agent_spec.get('department', 'operations'),
        'capabilities': agent_spec.get('capabilities', []),
        'status': 'created',
        'code_generated': True,
        'tests_passed': random.choice([True, False])
    }
    
    return new_agent


# Data processing tasks
@app.task(base=BoarderframeTask, name='data.process_batch')
def process_data_batch(batch_id: str, data: list) -> dict:
    """Process a batch of data"""
    print(f"Processing batch {batch_id} with {len(data)} items")
    
    # Simulate processing
    processed_count = 0
    errors = []
    
    for item in data:
        time.sleep(0.1)  # Simulate work
        if random.random() < 0.95:  # 95% success rate
            processed_count += 1
        else:
            errors.append(f"Failed to process item {item.get('id', 'unknown')}")
    
    return {
        'batch_id': batch_id,
        'total_items': len(data),
        'processed': processed_count,
        'errors': errors,
        'success_rate': processed_count / len(data) if data else 0
    }


# Workflow examples
@app.task(name='workflows.agent_consensus')
def agent_consensus_workflow():
    """Multi-agent consensus workflow"""
    # Create a chord: multiple agents analyze in parallel, then reach consensus
    workflow = chord(
        group(
            solomon_analyze_system.s({'cpu': 75, 'memory': 82, 'error_rate': 0.02}),
            david_strategic_planning.s({}, {}),
            adam_generate_agent.s({'name': 'Helper Bot', 'type': 'assistant'})
        ),
        build_consensus.s()
    )
    
    return workflow.apply_async()


@app.task(name='workflows.build_consensus')
def build_consensus(results: list) -> dict:
    """Build consensus from multiple agent results"""
    print(f"Building consensus from {len(results)} agent results")
    
    consensus = {
        'timestamp': datetime.utcnow().isoformat(),
        'participants': len(results),
        'unanimous': False,
        'recommendations': [],
        'action_items': []
    }
    
    # Analyze results
    for result in results:
        if 'recommendations' in result:
            consensus['recommendations'].extend(result['recommendations'])
        if 'priority_actions' in result:
            consensus['action_items'].extend(result['priority_actions'])
    
    # Remove duplicates
    consensus['recommendations'] = list(set(consensus['recommendations']))
    consensus['action_items'] = list(set(consensus['action_items']))
    
    return consensus


# Long-running task example
@app.task(base=BoarderframeTask, bind=True, name='analysis.deep_analysis')
def deep_analysis(self, dataset_id: str, analysis_type: str):
    """Long-running deep analysis task with progress updates"""
    print(f"Starting deep analysis of {dataset_id}")
    
    total_steps = 10
    
    for i in range(total_steps):
        # Update task state with progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': total_steps,
                'status': f'Analyzing step {i + 1}/{total_steps}'
            }
        )
        
        # Simulate work
        time.sleep(random.uniform(1, 3))
        
        # Random chance of retry
        if i == 5 and random.random() < 0.1:
            raise self.retry(exc=Exception("Temporary failure"), countdown=60)
    
    return {
        'dataset_id': dataset_id,
        'analysis_type': analysis_type,
        'insights': [
            'Pattern A detected with 87% confidence',
            'Anomaly in sector 7 requires attention',
            'Optimization opportunity identified'
        ],
        'completion_time': datetime.utcnow().isoformat()
    }


if __name__ == '__main__':
    print("Example tasks loaded. Use manage_workers.py to run these tasks.")
    
    # Example of submitting tasks
    from core.task_queue import get_task_manager, TaskPriority
    
    task_manager = get_task_manager()
    
    # Submit a high-priority Solomon analysis
    task_id = task_manager.submit_task(
        'agents.solomon.analyze_system',
        {'cpu': 85, 'memory': 90, 'error_rate': 0.15},
        priority=TaskPriority.HIGH
    )
    print(f"Submitted Solomon analysis: {task_id}")
    
    # Submit a workflow
    workflow_id = task_manager.submit_task(
        'workflows.agent_consensus',
        priority=TaskPriority.NORMAL
    )
    print(f"Submitted consensus workflow: {workflow_id}")
'''
    
    with open(example_file, 'w') as f:
        f.write(example_content)
    
    # Make executable
    example_file.chmod(0o755)
    
    print(f"  ✅ Created example tasks: {example_file}")
    return True


def create_task_queue_docs():
    """Create task queue documentation"""
    doc_content = """# Task Queue System

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
"""
    
    doc_file = Path("TASK_QUEUE.md")
    with open(doc_file, 'w') as f:
        f.write(doc_content)
    
    print(f"  ✅ Created task queue documentation: {doc_file}")
    return True


def create_task_dashboard():
    """Create a simple task queue dashboard"""
    dashboard_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Queue Dashboard - BoarderframeOS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            overflow-x: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);
            padding: 20px 40px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.5);
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(45deg, #9C27B0, #2196F3, #00BCD4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .container {
            padding: 20px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .queue-section {
            margin-bottom: 40px;
        }
        
        .queue-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .queue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .queue-name {
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .queue-length {
            background: #2196F3;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: #4CAF50;
            transition: width 0.3s ease;
        }
        
        .task-submit {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 40px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #aaa;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            color: white;
            font-size: 16px;
        }
        
        button {
            background: #2196F3;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        button:hover {
            background: #1976D2;
        }
        
        .task-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .task-item {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .task-status {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 600;
        }
        
        .status-pending { background: #FF9800; }
        .status-running { background: #2196F3; }
        .status-success { background: #4CAF50; }
        .status-failure { background: #F44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Task Queue Dashboard</h1>
        <p>Real-time monitoring of BoarderframeOS task processing</p>
    </div>
    
    <div class="container">
        <!-- Statistics -->
        <div class="stats-grid">
            <div class="stat-card">
                <div>Active Workers</div>
                <div class="stat-value" id="activeWorkers">0</div>
            </div>
            <div class="stat-card">
                <div>Active Tasks</div>
                <div class="stat-value" id="activeTasks">0</div>
            </div>
            <div class="stat-card">
                <div>Scheduled Tasks</div>
                <div class="stat-value" id="scheduledTasks">0</div>
            </div>
            <div class="stat-card">
                <div>Total Processed</div>
                <div class="stat-value" id="totalProcessed">0</div>
            </div>
        </div>
        
        <!-- Queue Status -->
        <div class="queue-section">
            <h2>Queue Status</h2>
            <div id="queueList">
                <!-- Queue cards will be inserted here -->
            </div>
        </div>
        
        <!-- Submit Task -->
        <div class="task-submit">
            <h2>Submit Task</h2>
            <form id="taskForm">
                <div class="form-group">
                    <label>Task Name</label>
                    <select id="taskName">
                        <option value="core.task_queue.agent_think">Agent Think</option>
                        <option value="core.task_queue.agent_act">Agent Act</option>
                        <option value="core.task_queue.llm_process">LLM Process</option>
                        <option value="core.task_queue.analytics_aggregate">Analytics Aggregate</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Priority</label>
                    <select id="priority">
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="normal" selected>Normal</option>
                        <option value="low">Low</option>
                        <option value="background">Background</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Arguments (JSON)</label>
                    <textarea id="taskArgs" rows="3">{"agent_id": "test-agent", "context": {}}</textarea>
                </div>
                <button type="submit">Submit Task</button>
            </form>
        </div>
        
        <!-- Recent Tasks -->
        <div>
            <h2>Recent Tasks</h2>
            <div class="task-list" id="taskList">
                <!-- Task items will be inserted here -->
            </div>
        </div>
    </div>
    
    <script>
        let recentTasks = [];
        
        async function fetchQueueStats() {
            try {
                const response = await fetch('/api/tasks');
                const data = await response.json();
                updateQueueDisplay(data.queue_stats);
            } catch (error) {
                console.error('Failed to fetch queue stats:', error);
            }
        }
        
        function updateQueueDisplay(stats) {
            // Update summary stats
            document.getElementById('activeTasks').textContent = stats.active || 0;
            document.getElementById('scheduledTasks').textContent = stats.scheduled || 0;
            
            // Update queue cards
            const queueList = document.getElementById('queueList');
            queueList.innerHTML = '';
            
            const queues = ['critical', 'high', 'default', 'low', 'agents', 'llm', 'analytics'];
            
            queues.forEach(queue => {
                const length = stats[`queue_${queue}`] || 0;
                const card = document.createElement('div');
                card.className = 'queue-card';
                
                card.innerHTML = `
                    <div class="queue-header">
                        <div class="queue-name">${queue.charAt(0).toUpperCase() + queue.slice(1)} Queue</div>
                        <div class="queue-length">${length}</div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${Math.min(length * 10, 100)}%"></div>
                    </div>
                `;
                
                queueList.appendChild(card);
            });
        }
        
        // Submit task form
        document.getElementById('taskForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const taskName = document.getElementById('taskName').value;
            const priority = document.getElementById('priority').value;
            const taskArgs = document.getElementById('taskArgs').value;
            
            try {
                const args = JSON.parse(taskArgs);
                
                const response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        task_name: taskName,
                        args: [args],
                        priority: priority
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    alert(`Task submitted: ${result.task_id}`);
                    recentTasks.unshift({
                        id: result.task_id,
                        name: taskName,
                        status: 'pending',
                        timestamp: new Date()
                    });
                    updateTaskList();
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert('Invalid JSON arguments');
            }
        });
        
        function updateTaskList() {
            const taskList = document.getElementById('taskList');
            taskList.innerHTML = '';
            
            recentTasks.slice(0, 10).forEach(task => {
                const item = document.createElement('div');
                item.className = 'task-item';
                
                item.innerHTML = `
                    <div>
                        <strong>${task.name}</strong><br>
                        <small>${task.id}</small>
                    </div>
                    <div class="task-status status-${task.status}">${task.status}</div>
                `;
                
                taskList.appendChild(item);
            });
        }
        
        // Initial load
        fetchQueueStats();
        
        // Auto-refresh
        setInterval(fetchQueueStats, 5000);
    </script>
</body>
</html>'''
    
    dashboard_file = Path("task_queue_dashboard.html")
    with open(dashboard_file, 'w') as f:
        f.write(dashboard_content)
    
    print(f"  ✅ Created task queue dashboard: {dashboard_file}")
    return True


def update_requirements():
    """Ensure Celery dependencies are in requirements.txt"""
    req_file = Path("requirements.txt")
    
    if not req_file.exists():
        print("  ⚠️  requirements.txt not found")
        return False
    
    try:
        with open(req_file, 'r') as f:
            requirements = f.read()
        
        # Check if Celery is already there
        if 'celery' in requirements:
            print("  ℹ️  Celery already in requirements.txt")
            return False
        
        # Add Celery dependencies
        celery_deps = """
# Task Queue
celery==5.3.4
redis==5.0.1
kombu==5.3.4
flower==2.0.1  # Optional: Celery monitoring dashboard
"""
        
        # Append to requirements
        with open(req_file, 'a') as f:
            f.write(celery_deps)
        
        print("  ✅ Updated requirements.txt with Celery dependencies")
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating requirements: {e}")
        return False


def main():
    """Main integration function"""
    print_header()
    
    # Check if we're in the right directory
    if not Path("startup.py").exists():
        print("❌ Error: Not in BoarderframeOS root directory")
        return False
    
    updated_files = []
    
    try:
        # Update core components
        print("🔧 Updating core components...")
        if update_base_agent():
            updated_files.append("core/base_agent.py")
        
        # Update Corporate HQ
        print("\n🏢 Updating Corporate HQ...")
        if update_corporate_hq():
            updated_files.append("corporate_headquarters.py")
        
        # Update startup
        print("\n🚀 Updating startup process...")
        if update_startup():
            updated_files.append("startup.py")
        
        # Create examples and docs
        print("\n📚 Creating examples and documentation...")
        create_example_tasks()
        create_task_queue_docs()
        create_task_dashboard()
        
        # Update requirements
        print("\n📦 Updating requirements...")
        update_requirements()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 TASK QUEUE INTEGRATION COMPLETE")
        print("=" * 60)
        print(f"Files updated: {len(updated_files)}")
        
        if updated_files:
            print("\n📁 Updated files:")
            for file in updated_files:
                print(f"  - {file}")
        
        print("\n🚀 Quick Start:")
        print("  1. Install dependencies: pip install celery redis kombu")
        print("  2. Start Redis: docker-compose up -d redis")
        print("  3. Start workers: ./manage_workers.py cluster")
        print("  4. View dashboard: open task_queue_dashboard.html")
        
        print("\n📊 Features Enabled:")
        print("  ✓ Distributed task processing")
        print("  ✓ Priority-based queues")
        print("  ✓ Agent task offloading")
        print("  ✓ Task monitoring API")
        print("  ✓ Example implementations")
        print("  ✓ Comprehensive documentation")
        
        print("\n💡 Next Steps:")
        print("  - Test with: python example_tasks.py")
        print("  - Monitor with: ./manage_workers.py monitor")
        print("  - Submit tasks via Corporate HQ API")
        
        print("\n✅ Task queue system is ready!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)