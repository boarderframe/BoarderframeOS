#!/usr/bin/env python3
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
