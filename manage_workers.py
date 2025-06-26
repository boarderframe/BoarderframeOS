#!/usr/bin/env python3
"""
Celery Worker Management for BoarderframeOS
Manage and monitor Celery workers
"""

import click
import subprocess
import os
import sys
import signal
import time
import json
import psutil
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.task_queue import app, get_task_manager, TaskPriority

# Get the celery executable path
def get_celery_path():
    """Get the path to the celery executable"""
    # First try the virtual environment
    venv_celery = Path(sys.executable).parent / "celery"
    if venv_celery.exists():
        return str(venv_celery)
    
    # Try using sys.executable with -m celery
    return [sys.executable, "-m", "celery"]


@click.group()
@click.pass_context
def cli(ctx):
    """BoarderframeOS Celery Worker Management"""
    ctx.ensure_object(dict)
    

@cli.command()
@click.option('--queues', '-q', multiple=True, default=['default'], 
              help='Queues to process (critical, high, default, low, agents, llm, analytics)')
@click.option('--concurrency', '-c', type=int, default=4, help='Worker concurrency')
@click.option('--loglevel', '-l', default='info', 
              type=click.Choice(['debug', 'info', 'warning', 'error']))
@click.option('--hostname', '-n', help='Set custom hostname')
@click.option('--detach', '-d', is_flag=True, help='Run in background')
@click.pass_context
def start(ctx, queues, concurrency, loglevel, hostname, detach):
    """Start Celery worker"""
    click.echo(f"🚀 Starting Celery worker...")
    
    # Build command
    celery_cmd = get_celery_path()
    if isinstance(celery_cmd, list):
        cmd = celery_cmd + ['-A', 'core.task_queue', 'worker']
    else:
        cmd = [celery_cmd, '-A', 'core.task_queue', 'worker']
    
    cmd.extend([
        '--loglevel', loglevel,
        '--concurrency', str(concurrency),
        '--queues', ','.join(queues)
    ])
    
    if hostname:
        cmd.extend(['--hostname', hostname])
    else:
        cmd.extend(['--hostname', f'worker@{os.uname().nodename}'])
    
    # Add optimization flags
    cmd.extend([
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat',
        '--prefetch-multiplier', '4',
        '--max-tasks-per-child', '1000'
    ])
    
    if detach:
        # Run in background
        pid_file = Path('celery_worker.pid')
        log_file = Path('logs/celery_worker.log')
        log_file.parent.mkdir(exist_ok=True)
        
        process = subprocess.Popen(
            cmd,
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        
        # Save PID
        pid_file.write_text(str(process.pid))
        
        click.echo(f"✅ Worker started in background (PID: {process.pid})")
        click.echo(f"📋 Logs: {log_file}")
    else:
        # Run in foreground
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            click.echo("\n🛑 Worker stopped")


@cli.command()
@click.option('--all', '-a', is_flag=True, help='Stop all workers')
@click.pass_context
def stop(ctx, all):
    """Stop Celery workers"""
    if all:
        click.echo("🛑 Stopping all Celery workers...")
        celery_cmd = get_celery_path()
        if isinstance(celery_cmd, list):
            subprocess.run(celery_cmd + ['-A', 'core.task_queue', 'control', 'shutdown'])
        else:
            subprocess.run([celery_cmd, '-A', 'core.task_queue', 'control', 'shutdown'])
        click.echo("✅ All workers stopped")
    else:
        # Stop worker from PID file
        pid_file = Path('celery_worker.pid')
        if pid_file.exists():
            pid = int(pid_file.read_text())
            try:
                os.kill(pid, signal.SIGTERM)
                click.echo(f"✅ Worker stopped (PID: {pid})")
                pid_file.unlink()
            except ProcessLookupError:
                click.echo("⚠️  Worker not running")
                pid_file.unlink()
        else:
            click.echo("⚠️  No worker PID file found")


@cli.command()
@click.option('--detach', '-d', is_flag=True, help='Run in background')
@click.pass_context
def beat(ctx, detach):
    """Start Celery beat scheduler"""
    click.echo("⏰ Starting Celery beat scheduler...")
    
    celery_cmd = get_celery_path()
    if isinstance(celery_cmd, list):
        cmd = celery_cmd + ['-A', 'core.task_queue', 'beat', '--loglevel', 'info']
    else:
        cmd = [celery_cmd, '-A', 'core.task_queue', 'beat', '--loglevel', 'info']
    
    if detach:
        pid_file = Path('celery_beat.pid')
        log_file = Path('logs/celery_beat.log')
        log_file.parent.mkdir(exist_ok=True)
        
        process = subprocess.Popen(
            cmd,
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        
        pid_file.write_text(str(process.pid))
        
        click.echo(f"✅ Beat scheduler started (PID: {process.pid})")
    else:
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            click.echo("\n🛑 Beat scheduler stopped")


@cli.command()
@click.pass_context
def status(ctx):
    """Show worker status"""
    click.echo("📊 Celery Worker Status")
    click.echo("=" * 50)
    
    # Check if workers are running
    celery_cmd = get_celery_path()
    if isinstance(celery_cmd, list):
        result = subprocess.run(
            celery_cmd + ['-A', 'core.task_queue', 'inspect', 'stats'],
            capture_output=True,
            text=True
        )
    else:
        result = subprocess.run(
            [celery_cmd, '-A', 'core.task_queue', 'inspect', 'stats'],
            capture_output=True,
            text=True
        )
    
    if result.returncode == 0:
        try:
            stats = json.loads(result.stdout)
            
            for worker_name, worker_stats in stats.items():
                click.echo(f"\n🤖 Worker: {worker_name}")
                click.echo(f"  Pool: {worker_stats.get('pool', {}).get('implementation', 'N/A')}")
                click.echo(f"  Max concurrency: {worker_stats.get('pool', {}).get('max-concurrency', 'N/A')}")
                click.echo(f"  Current tasks: {worker_stats.get('total', {})}")
                
                if 'rusage' in worker_stats:
                    rusage = worker_stats['rusage']
                    click.echo(f"  CPU time: {rusage.get('utime', 0):.2f}s user, {rusage.get('stime', 0):.2f}s system")
                
        except json.JSONDecodeError:
            click.echo("⚠️  Could not parse worker stats")
    else:
        click.echo("❌ No workers running")
    
    # Show queue stats
    click.echo("\n📬 Queue Statistics:")
    task_manager = get_task_manager()
    queue_stats = task_manager.get_queue_stats()
    
    for key, value in queue_stats.items():
        click.echo(f"  {key}: {value}")


@cli.command()
@click.option('--queue', '-q', help='Filter by queue')
@click.option('--limit', '-l', type=int, default=10, help='Number of tasks to show')
@click.pass_context
def tasks(ctx, queue, limit):
    """List active tasks"""
    click.echo("📋 Active Tasks")
    click.echo("=" * 50)
    
    # Get active tasks
    celery_cmd = get_celery_path()
    if isinstance(celery_cmd, list):
        result = subprocess.run(
            celery_cmd + ['-A', 'core.task_queue', 'inspect', 'active'],
            capture_output=True,
            text=True
        )
    else:
        result = subprocess.run(
            [celery_cmd, '-A', 'core.task_queue', 'inspect', 'active'],
            capture_output=True,
            text=True
        )
    
    if result.returncode == 0:
        try:
            active_tasks = json.loads(result.stdout)
            
            count = 0
            for worker_name, tasks in active_tasks.items():
                for task in tasks:
                    if queue and task.get('delivery_info', {}).get('routing_key') != queue:
                        continue
                    
                    click.echo(f"\nTask ID: {task['id']}")
                    click.echo(f"  Name: {task['name']}")
                    click.echo(f"  Worker: {worker_name}")
                    click.echo(f"  Args: {task.get('args', [])}")
                    click.echo(f"  Started: {task.get('time_start', 'N/A')}")
                    
                    count += 1
                    if count >= limit:
                        return
                        
            if count == 0:
                click.echo("No active tasks found")
                
        except json.JSONDecodeError:
            click.echo("⚠️  Could not parse active tasks")
    else:
        click.echo("❌ Could not fetch active tasks")


@cli.command()
@click.argument('task_id')
@click.pass_context
def cancel(ctx, task_id):
    """Cancel a task"""
    task_manager = get_task_manager()
    
    try:
        task_manager.cancel_task(task_id)
        click.echo(f"✅ Task {task_id} cancelled")
    except Exception as e:
        click.echo(f"❌ Failed to cancel task: {e}")


@cli.command()
@click.argument('task_name')
@click.argument('args', nargs=-1)
@click.option('--priority', '-p', 
              type=click.Choice(['critical', 'high', 'normal', 'low', 'background']),
              default='normal')
@click.pass_context
def submit(ctx, task_name, args, priority):
    """Submit a task"""
    task_manager = get_task_manager()
    
    # Map priority
    priority_map = {
        'critical': TaskPriority.CRITICAL,
        'high': TaskPriority.HIGH,
        'normal': TaskPriority.NORMAL,
        'low': TaskPriority.LOW,
        'background': TaskPriority.BACKGROUND
    }
    
    try:
        # Parse args as JSON if possible
        parsed_args = []
        for arg in args:
            try:
                parsed_args.append(json.loads(arg))
            except json.JSONDecodeError:
                parsed_args.append(arg)
        
        task_id = task_manager.submit_task(
            task_name,
            *parsed_args,
            priority=priority_map[priority]
        )
        
        click.echo(f"✅ Task submitted: {task_id}")
        click.echo(f"   Name: {task_name}")
        click.echo(f"   Priority: {priority}")
        click.echo(f"   Args: {parsed_args}")
        
    except Exception as e:
        click.echo(f"❌ Failed to submit task: {e}")


@cli.command()
@click.argument('task_id')
@click.pass_context
def result(ctx, task_id):
    """Get task result"""
    task_manager = get_task_manager()
    
    try:
        task_result = task_manager.get_task_status(task_id)
        
        click.echo(f"📊 Task Result: {task_id}")
        click.echo("=" * 50)
        click.echo(f"Status: {task_result.status.value}")
        
        if task_result.result:
            click.echo(f"Result: {json.dumps(task_result.result, indent=2)}")
        
        if task_result.error:
            click.echo(f"Error: {task_result.error}")
        
        if task_result.start_time:
            click.echo(f"Started: {task_result.start_time}")
        
        if task_result.end_time:
            click.echo(f"Ended: {task_result.end_time}")
        
        if task_result.duration:
            click.echo(f"Duration: {task_result.duration:.2f}s")
            
    except Exception as e:
        click.echo(f"❌ Failed to get result: {e}")


@cli.command()
@click.pass_context
def monitor(ctx):
    """Monitor workers in real-time"""
    click.echo("📊 Real-time Worker Monitor (Press Ctrl+C to exit)")
    click.echo("=" * 60)
    
    try:
        while True:
            # Clear screen
            click.clear()
            
            click.echo(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo("=" * 60)
            
            # Get worker stats
            celery_cmd = get_celery_path()
            if isinstance(celery_cmd, list):
                result = subprocess.run(
                    celery_cmd + ['-A', 'core.task_queue', 'inspect', 'stats'],
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    [celery_cmd, '-A', 'core.task_queue', 'inspect', 'stats'],
                    capture_output=True,
                    text=True
                )
            
            if result.returncode == 0:
                try:
                    stats = json.loads(result.stdout)
                    
                    # Show worker summary
                    click.echo(f"\n👷 Active Workers: {len(stats)}")
                    
                    total_tasks = 0
                    for worker_name, worker_stats in stats.items():
                        total = worker_stats.get('total', {})
                        total_tasks += sum(total.values())
                        
                        click.echo(f"\n  {worker_name}:")
                        click.echo(f"    Tasks: {total}")
                        
                        # Show process info if available
                        pid = worker_stats.get('pid')
                        if pid:
                            try:
                                process = psutil.Process(pid)
                                click.echo(f"    CPU: {process.cpu_percent()}%")
                                click.echo(f"    Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
                            except:
                                pass
                    
                    click.echo(f"\n📈 Total Tasks Processed: {total_tasks}")
                    
                except json.JSONDecodeError:
                    click.echo("⚠️  Could not parse stats")
            else:
                click.echo("❌ No workers detected")
            
            # Show queue lengths
            task_manager = get_task_manager()
            queue_stats = task_manager.get_queue_stats()
            
            click.echo("\n📬 Queue Lengths:")
            for queue in ['critical', 'high', 'default', 'low']:
                length = queue_stats.get(f'queue_{queue}', 0)
                bar = '█' * min(length, 20)
                click.echo(f"  {queue:10s}: {bar} ({length})")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        click.echo("\n\n✅ Monitor stopped")


@cli.command()
@click.option('--workers', '-w', type=int, default=2, help='Number of workers')
@click.option('--include-beat', '-b', is_flag=True, help='Also start beat scheduler')
@click.pass_context
def cluster(ctx, workers, include_beat):
    """Start a cluster of workers"""
    click.echo(f"🚀 Starting Celery cluster with {workers} workers...")
    
    processes = []
    
    # Start workers
    for i in range(workers):
        hostname = f'worker{i}@{os.uname().nodename}'
        
        # Assign different queues to workers
        if i == 0:
            queues = ['critical', 'high', 'default']
        elif i == 1:
            queues = ['agents', 'llm']
        else:
            queues = ['low', 'analytics']
        
        celery_cmd = get_celery_path()
        if isinstance(celery_cmd, list):
            cmd = celery_cmd + ['-A', 'core.task_queue', 'worker']
        else:
            cmd = [celery_cmd, '-A', 'core.task_queue', 'worker']
        
        cmd.extend([
            '--hostname', hostname,
            '--queues', ','.join(queues),
            '--concurrency', '4',
            '--loglevel', 'info'
        ])
        
        log_file = Path(f'logs/celery_worker_{i}.log')
        log_file.parent.mkdir(exist_ok=True)
        
        process = subprocess.Popen(
            cmd,
            stdout=open(log_file, 'a'),
            stderr=subprocess.STDOUT
        )
        
        processes.append((process, hostname))
        click.echo(f"  ✅ Started {hostname} (PID: {process.pid})")
    
    # Start beat if requested
    if include_beat:
        celery_cmd = get_celery_path()
        if isinstance(celery_cmd, list):
            beat_cmd = celery_cmd + ['-A', 'core.task_queue', 'beat', '--loglevel', 'info']
        else:
            beat_cmd = [celery_cmd, '-A', 'core.task_queue', 'beat', '--loglevel', 'info']
        
        beat_log = Path('logs/celery_beat.log')
        beat_process = subprocess.Popen(
            beat_cmd,
            stdout=open(beat_log, 'a'),
            stderr=subprocess.STDOUT
        )
        
        processes.append((beat_process, 'beat'))
        click.echo(f"  ✅ Started beat scheduler (PID: {beat_process.pid})")
    
    click.echo("\n✅ Cluster started. Press Ctrl+C to stop all workers.")
    
    try:
        # Wait for interruption
        for process, name in processes:
            process.wait()
    except KeyboardInterrupt:
        click.echo("\n🛑 Stopping cluster...")
        
        for process, name in processes:
            process.terminate()
            click.echo(f"  ✅ Stopped {name}")
        
        # Wait for processes to exit
        for process, name in processes:
            process.wait()
        
        click.echo("✅ Cluster stopped")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n❌ Cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)