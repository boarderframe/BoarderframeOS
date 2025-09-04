#!/usr/bin/env python3
"""
Performance Optimization Test Suite for MCP-UI System
Tests all performance features and generates benchmarks
"""
import asyncio
import time
import json
import statistics
from typing import Dict, Any, List
from datetime import datetime

import aiohttp
import uvloop  # High-performance event loop
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

console = Console()


class PerformanceTester:
    """Comprehensive performance testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        
    async def test_response_times(self, endpoints: List[str], iterations: int = 100):
        """Test response times for endpoints"""
        console.print("\n[bold blue]Testing Response Times[/bold blue]")
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                times = []
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(f"Testing {endpoint}", total=iterations)
                    
                    for _ in range(iterations):
                        start = time.perf_counter()
                        try:
                            async with session.get(f"{self.base_url}{endpoint}") as response:
                                await response.read()
                                elapsed = (time.perf_counter() - start) * 1000  # ms
                                times.append(elapsed)
                        except Exception as e:
                            console.print(f"[red]Error testing {endpoint}: {e}[/red]")
                            
                        progress.update(task, advance=1)
                        
                if times:
                    results[endpoint] = {
                        'min': min(times),
                        'max': max(times),
                        'mean': statistics.mean(times),
                        'median': statistics.median(times),
                        'p95': statistics.quantiles(times, n=20)[18] if len(times) > 1 else times[0],
                        'p99': statistics.quantiles(times, n=100)[98] if len(times) > 1 else times[0],
                        'samples': len(times)
                    }
                    
        return results
        
    async def test_cache_performance(self):
        """Test cache hit rates and performance"""
        console.print("\n[bold blue]Testing Cache Performance[/bold blue]")
        
        endpoint = "/api/v1/servers"
        results = {
            'cold_cache': [],
            'warm_cache': []
        }
        
        async with aiohttp.ClientSession() as session:
            # Clear cache first (if endpoint available)
            try:
                await session.post(f"{self.base_url}/api/v1/cache/clear")
            except:
                pass
                
            # Cold cache test
            for _ in range(10):
                start = time.perf_counter()
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    await response.read()
                    cache_status = response.headers.get('X-Cache', 'UNKNOWN')
                    elapsed = (time.perf_counter() - start) * 1000
                    results['cold_cache'].append({
                        'time': elapsed,
                        'cache': cache_status
                    })
                    
            # Warm cache test
            for _ in range(10):
                start = time.perf_counter()
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    await response.read()
                    cache_status = response.headers.get('X-Cache', 'UNKNOWN')
                    elapsed = (time.perf_counter() - start) * 1000
                    results['warm_cache'].append({
                        'time': elapsed,
                        'cache': cache_status
                    })
                    
        return results
        
    async def test_compression(self):
        """Test compression effectiveness"""
        console.print("\n[bold blue]Testing Compression[/bold blue]")
        
        results = {}
        endpoints = [
            "/api/v1/servers",
            "/api/v1/metrics",
            "/static/js/app.js"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                # Test without compression
                headers_no_comp = {'Accept-Encoding': 'identity'}
                async with session.get(f"{self.base_url}{endpoint}", 
                                      headers=headers_no_comp) as response:
                    uncompressed_size = len(await response.read())
                    
                # Test with compression
                headers_comp = {'Accept-Encoding': 'gzip, br, deflate'}
                async with session.get(f"{self.base_url}{endpoint}", 
                                      headers=headers_comp) as response:
                    compressed_size = len(await response.read())
                    encoding = response.headers.get('Content-Encoding', 'none')
                    
                savings = ((uncompressed_size - compressed_size) / uncompressed_size * 100 
                          if uncompressed_size > 0 else 0)
                
                results[endpoint] = {
                    'uncompressed_size': uncompressed_size,
                    'compressed_size': compressed_size,
                    'encoding': encoding,
                    'savings_percent': savings
                }
                
        return results
        
    async def test_concurrent_load(self, concurrent: int = 50, duration: int = 10):
        """Test system under concurrent load"""
        console.print(f"\n[bold blue]Testing Concurrent Load ({concurrent} users, {duration}s)[/bold blue]")
        
        start_time = time.time()
        successful = 0
        failed = 0
        response_times = []
        
        async def make_request(session):
            nonlocal successful, failed
            
            while time.time() - start_time < duration:
                try:
                    req_start = time.perf_counter()
                    async with session.get(f"{self.base_url}/api/v1/health") as response:
                        await response.read()
                        elapsed = (time.perf_counter() - req_start) * 1000
                        response_times.append(elapsed)
                        
                        if response.status == 200:
                            successful += 1
                        else:
                            failed += 1
                except:
                    failed += 1
                    
                await asyncio.sleep(0.1)  # Small delay between requests
                
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session) for _ in range(concurrent)]
            await asyncio.gather(*tasks)
            
        total_requests = successful + failed
        actual_duration = time.time() - start_time
        
        return {
            'concurrent_users': concurrent,
            'duration': actual_duration,
            'total_requests': total_requests,
            'successful': successful,
            'failed': failed,
            'requests_per_second': total_requests / actual_duration if actual_duration > 0 else 0,
            'error_rate': (failed / total_requests * 100) if total_requests > 0 else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else 0
        }
        
    async def test_web_vitals(self):
        """Simulate web vitals collection"""
        console.print("\n[bold blue]Testing Web Vitals Collection[/bold blue]")
        
        # Simulate sending web vitals
        vitals = [
            {'metric': 'LCP', 'value': 2400, 'page': '/'},
            {'metric': 'FID', 'value': 95, 'page': '/'},
            {'metric': 'CLS', 'value': 0.08, 'page': '/'},
            {'metric': 'FCP', 'value': 1700, 'page': '/'},
            {'metric': 'TTFB', 'value': 750, 'page': '/'}
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for vital in vitals:
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/analytics/vitals",
                        json=vital
                    ) as response:
                        results.append({
                            'metric': vital['metric'],
                            'value': vital['value'],
                            'accepted': response.status == 200
                        })
                except Exception as e:
                    results.append({
                        'metric': vital['metric'],
                        'value': vital['value'],
                        'accepted': False,
                        'error': str(e)
                    })
                    
        return results
        
    def generate_report(self, results: Dict[str, Any]):
        """Generate performance report"""
        console.print("\n[bold green]Performance Test Report[/bold green]")
        console.print(f"Generated at: {datetime.now().isoformat()}\n")
        
        # Response Times Table
        if 'response_times' in results:
            table = Table(title="Response Times (ms)")
            table.add_column("Endpoint", style="cyan")
            table.add_column("Min", justify="right")
            table.add_column("Mean", justify="right")
            table.add_column("Median", justify="right")
            table.add_column("P95", justify="right")
            table.add_column("P99", justify="right")
            table.add_column("Max", justify="right")
            
            for endpoint, metrics in results['response_times'].items():
                table.add_row(
                    endpoint,
                    f"{metrics['min']:.2f}",
                    f"{metrics['mean']:.2f}",
                    f"{metrics['median']:.2f}",
                    f"{metrics['p95']:.2f}",
                    f"{metrics['p99']:.2f}",
                    f"{metrics['max']:.2f}"
                )
                
            console.print(table)
            
        # Cache Performance
        if 'cache_performance' in results:
            cache_data = results['cache_performance']
            
            cold_times = [r['time'] for r in cache_data['cold_cache']]
            warm_times = [r['time'] for r in cache_data['warm_cache']]
            
            console.print("\n[bold]Cache Performance:[/bold]")
            console.print(f"  Cold Cache Avg: {statistics.mean(cold_times):.2f}ms")
            console.print(f"  Warm Cache Avg: {statistics.mean(warm_times):.2f}ms")
            
            speedup = statistics.mean(cold_times) / statistics.mean(warm_times) if warm_times else 1
            console.print(f"  Cache Speedup: {speedup:.2f}x")
            
        # Compression Results
        if 'compression' in results:
            table = Table(title="Compression Effectiveness")
            table.add_column("Endpoint", style="cyan")
            table.add_column("Original Size", justify="right")
            table.add_column("Compressed Size", justify="right")
            table.add_column("Encoding")
            table.add_column("Savings %", justify="right")
            
            for endpoint, metrics in results['compression'].items():
                table.add_row(
                    endpoint,
                    f"{metrics['uncompressed_size']:,}",
                    f"{metrics['compressed_size']:,}",
                    metrics['encoding'],
                    f"{metrics['savings_percent']:.1f}%"
                )
                
            console.print(table)
            
        # Load Test Results
        if 'load_test' in results:
            load = results['load_test']
            console.print("\n[bold]Load Test Results:[/bold]")
            console.print(f"  Concurrent Users: {load['concurrent_users']}")
            console.print(f"  Duration: {load['duration']:.2f}s")
            console.print(f"  Total Requests: {load['total_requests']:,}")
            console.print(f"  Requests/Second: {load['requests_per_second']:.2f}")
            console.print(f"  Error Rate: {load['error_rate']:.2f}%")
            console.print(f"  Avg Response Time: {load['avg_response_time']:.2f}ms")
            console.print(f"  P95 Response Time: {load['p95_response_time']:.2f}ms")
            
        # Performance Score
        self.calculate_performance_score(results)
        
    def calculate_performance_score(self, results: Dict[str, Any]):
        """Calculate overall performance score"""
        score = 100.0
        
        # Check response times
        if 'response_times' in results:
            for endpoint, metrics in results['response_times'].items():
                if metrics['p95'] > 200:  # Target: < 200ms
                    score -= 10
                if metrics['p99'] > 500:  # Target: < 500ms
                    score -= 5
                    
        # Check load test
        if 'load_test' in results:
            load = results['load_test']
            if load['error_rate'] > 1:  # Target: < 1% errors
                score -= 15
            if load['avg_response_time'] > 200:  # Target: < 200ms avg
                score -= 10
                
        # Check compression
        if 'compression' in results:
            avg_savings = statistics.mean([
                m['savings_percent'] for m in results['compression'].values()
            ])
            if avg_savings < 50:  # Target: > 50% compression
                score -= 5
                
        score = max(0, score)
        
        # Determine grade
        if score >= 90:
            grade = 'A'
            color = 'green'
        elif score >= 80:
            grade = 'B'
            color = 'yellow'
        elif score >= 70:
            grade = 'C'
            color = 'yellow'
        elif score >= 60:
            grade = 'D'
            color = 'red'
        else:
            grade = 'F'
            color = 'red'
            
        console.print(f"\n[bold]Overall Performance Score: [{color}]{score:.1f}/100 (Grade: {grade})[/{color}][/bold]")
        
        # Recommendations
        if score < 100:
            console.print("\n[bold]Recommendations:[/bold]")
            if 'response_times' in results:
                slow_endpoints = [
                    ep for ep, m in results['response_times'].items() 
                    if m['p95'] > 200
                ]
                if slow_endpoints:
                    console.print(f"  • Optimize slow endpoints: {', '.join(slow_endpoints)}")
                    
            if 'load_test' in results and results['load_test']['error_rate'] > 1:
                console.print("  • Investigate and fix errors under load")
                
            if 'compression' in results:
                uncompressed = [
                    ep for ep, m in results['compression'].items()
                    if m['savings_percent'] < 30
                ]
                if uncompressed:
                    console.print(f"  • Improve compression for: {', '.join(uncompressed)}")


async def main():
    """Run performance tests"""
    tester = PerformanceTester()
    results = {}
    
    # Test response times
    endpoints = [
        "/api/v1/health",
        "/api/v1/servers",
        "/api/v1/metrics"
    ]
    results['response_times'] = await tester.test_response_times(endpoints, iterations=50)
    
    # Test cache performance
    results['cache_performance'] = await tester.test_cache_performance()
    
    # Test compression
    results['compression'] = await tester.test_compression()
    
    # Test concurrent load
    results['load_test'] = await tester.test_concurrent_load(concurrent=25, duration=10)
    
    # Test web vitals
    results['web_vitals'] = await tester.test_web_vitals()
    
    # Generate report
    tester.generate_report(results)
    
    # Save results to file
    with open('performance_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    console.print("\n[green]Results saved to performance_test_results.json[/green]")


if __name__ == "__main__":
    console.print("[bold cyan]MCP-UI Performance Test Suite[/bold cyan]")
    console.print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Test failed: {e}[/red]")
        raise