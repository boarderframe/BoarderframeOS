"""
Real-time Performance Monitoring for MCP-UI System
Implements Core Web Vitals, user experience tracking, and automated testing
"""
import asyncio
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import statistics

from fastapi import Request, Response, WebSocket
from fastapi.responses import JSONResponse
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, Summary


@dataclass
class WebVital:
    """Core Web Vital metric"""
    name: str
    value: float
    rating: str  # good, needs-improvement, poor
    timestamp: float
    page_url: str
    user_agent: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CoreWebVitalsTracker:
    """Track Core Web Vitals for user experience"""
    
    # Thresholds based on Google's recommendations
    THRESHOLDS = {
        'LCP': {'good': 2500, 'poor': 4000},  # Largest Contentful Paint (ms)
        'FID': {'good': 100, 'poor': 300},    # First Input Delay (ms)
        'CLS': {'good': 0.1, 'poor': 0.25},   # Cumulative Layout Shift (score)
        'FCP': {'good': 1800, 'poor': 3000},  # First Contentful Paint (ms)
        'TTFB': {'good': 800, 'poor': 1800},  # Time to First Byte (ms)
        'INP': {'good': 200, 'poor': 500}     # Interaction to Next Paint (ms)
    }
    
    def __init__(self):
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.page_metrics: Dict[str, Dict] = {}
        
        # Prometheus metrics
        self.lcp_histogram = Histogram(
            'web_vitals_lcp_seconds',
            'Largest Contentful Paint',
            ['page', 'rating'],
            buckets=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 10.0]
        )
        
        self.fid_histogram = Histogram(
            'web_vitals_fid_milliseconds',
            'First Input Delay',
            ['page', 'rating'],
            buckets=[10, 25, 50, 100, 200, 300, 500, 1000]
        )
        
        self.cls_histogram = Histogram(
            'web_vitals_cls_score',
            'Cumulative Layout Shift',
            ['page', 'rating'],
            buckets=[0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.5, 1.0]
        )
        
    def record_vital(self, vital: WebVital):
        """Record a web vital metric"""
        key = f"{vital.name}:{vital.page_url}"
        self.metrics_buffer[key].append(vital)
        
        # Update Prometheus metrics
        if vital.name == 'LCP':
            self.lcp_histogram.labels(
                page=vital.page_url,
                rating=vital.rating
            ).observe(vital.value / 1000)  # Convert to seconds
        elif vital.name == 'FID':
            self.fid_histogram.labels(
                page=vital.page_url,
                rating=vital.rating
            ).observe(vital.value)
        elif vital.name == 'CLS':
            self.cls_histogram.labels(
                page=vital.page_url,
                rating=vital.rating
            ).observe(vital.value)
            
    def get_rating(self, metric_name: str, value: float) -> str:
        """Get rating for metric value"""
        if metric_name not in self.THRESHOLDS:
            return 'unknown'
            
        thresholds = self.THRESHOLDS[metric_name]
        if value <= thresholds['good']:
            return 'good'
        elif value <= thresholds['poor']:
            return 'needs-improvement'
        else:
            return 'poor'
            
    def get_page_score(self, page_url: str) -> Dict[str, Any]:
        """Calculate overall page performance score"""
        scores = {}
        
        for metric_name in ['LCP', 'FID', 'CLS']:
            key = f"{metric_name}:{page_url}"
            if key in self.metrics_buffer:
                values = [v.value for v in self.metrics_buffer[key]]
                if values:
                    # Use 75th percentile as recommended by Google
                    p75 = statistics.quantiles(values, n=4)[2] if len(values) > 1 else values[0]
                    rating = self.get_rating(metric_name, p75)
                    scores[metric_name] = {
                        'p75': p75,
                        'rating': rating,
                        'samples': len(values)
                    }
                    
        # Calculate overall score (all metrics must be good)
        overall_good = all(
            score.get('rating') == 'good' 
            for score in scores.values()
        )
        
        return {
            'page_url': page_url,
            'metrics': scores,
            'overall_rating': 'good' if overall_good else 'needs-improvement',
            'timestamp': datetime.now().isoformat()
        }
        
    def get_vitals_summary(self) -> Dict[str, Any]:
        """Get summary of all web vitals"""
        summary = {
            'pages': {},
            'overall': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Aggregate by page
        pages = set()
        for key in self.metrics_buffer.keys():
            _, page_url = key.split(':', 1)
            pages.add(page_url)
            
        for page_url in pages:
            summary['pages'][page_url] = self.get_page_score(page_url)
            
        # Calculate overall metrics
        for metric_name in ['LCP', 'FID', 'CLS']:
            all_values = []
            for key, vitals in self.metrics_buffer.items():
                if key.startswith(f"{metric_name}:"):
                    all_values.extend([v.value for v in vitals])
                    
            if all_values:
                summary['overall'][metric_name] = {
                    'p50': statistics.median(all_values),
                    'p75': statistics.quantiles(all_values, n=4)[2] if len(all_values) > 1 else all_values[0],
                    'p95': statistics.quantiles(all_values, n=20)[18] if len(all_values) > 1 else all_values[0],
                    'samples': len(all_values)
                }
                
        return summary


class RealTimeMetricsCollector:
    """Collect and stream real-time performance metrics"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.metrics_queue = asyncio.Queue()
        self.aggregated_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Real-time counters
        self.request_counter = Counter(
            'realtime_requests_total',
            'Total requests in real-time',
            ['method', 'path', 'status']
        )
        
        self.active_users = Gauge(
            'realtime_active_users',
            'Currently active users'
        )
        
        self.response_time = Summary(
            'realtime_response_time_seconds',
            'Response time summary',
            ['endpoint']
        )
        
    async def connect_websocket(self, websocket: WebSocket):
        """Connect client for real-time metrics"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.active_users.inc()
        
        # Send initial metrics
        await websocket.send_json(self.get_current_metrics())
        
    def disconnect_websocket(self, websocket: WebSocket):
        """Disconnect client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.active_users.dec()
            
    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """Broadcast metrics to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(metrics)
            except:
                disconnected.append(connection)
                
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect_websocket(conn)
            
    async def record_request_metric(self, method: str, path: str, 
                                   status: int, duration: float):
        """Record request metric"""
        self.request_counter.labels(
            method=method,
            path=path,
            status=str(status)
        ).inc()
        
        self.response_time.labels(endpoint=path).observe(duration)
        
        # Add to aggregated metrics
        metric = {
            'timestamp': time.time(),
            'method': method,
            'path': path,
            'status': status,
            'duration': duration
        }
        
        self.aggregated_metrics['requests'].append(metric)
        
        # Queue for broadcasting
        await self.metrics_queue.put(metric)
        
    async def metrics_broadcaster(self):
        """Background task to broadcast metrics"""
        while True:
            try:
                # Collect metrics from queue
                metrics_batch = []
                
                # Get up to 10 metrics with timeout
                for _ in range(10):
                    try:
                        metric = await asyncio.wait_for(
                            self.metrics_queue.get(),
                            timeout=0.1
                        )
                        metrics_batch.append(metric)
                    except asyncio.TimeoutError:
                        break
                        
                if metrics_batch:
                    # Broadcast to clients
                    await self.broadcast_metrics({
                        'type': 'metrics_update',
                        'data': metrics_batch,
                        'summary': self.get_current_metrics()
                    })
                    
                await asyncio.sleep(1)  # Broadcast every second
                
            except Exception as e:
                print(f"Broadcaster error: {e}")
                await asyncio.sleep(5)
                
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        requests = list(self.aggregated_metrics['requests'])
        
        if requests:
            recent_requests = requests[-100:]  # Last 100 requests
            durations = [r['duration'] for r in recent_requests]
            
            return {
                'requests_per_second': self._calculate_rps(recent_requests),
                'average_response_time': statistics.mean(durations),
                'p50_response_time': statistics.median(durations),
                'p95_response_time': statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
                'p99_response_time': statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0],
                'active_users': self.active_users._value.get(),
                'error_rate': self._calculate_error_rate(recent_requests),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'requests_per_second': 0,
                'average_response_time': 0,
                'active_users': self.active_users._value.get(),
                'error_rate': 0,
                'timestamp': datetime.now().isoformat()
            }
            
    def _calculate_rps(self, requests: List[Dict]) -> float:
        """Calculate requests per second"""
        if len(requests) < 2:
            return 0
            
        time_span = requests[-1]['timestamp'] - requests[0]['timestamp']
        if time_span > 0:
            return len(requests) / time_span
        return 0
        
    def _calculate_error_rate(self, requests: List[Dict]) -> float:
        """Calculate error rate percentage"""
        if not requests:
            return 0
            
        errors = sum(1 for r in requests if r['status'] >= 400)
        return (errors / len(requests)) * 100


class PerformanceTestRunner:
    """Automated performance testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[Dict] = []
        
    async def run_load_test(self, endpoint: str, concurrent_users: int = 10,
                           duration_seconds: int = 60) -> Dict[str, Any]:
        """Run load test on endpoint"""
        start_time = time.time()
        results = []
        
        async def make_request():
            async with aiohttp.ClientSession() as session:
                while time.time() - start_time < duration_seconds:
                    request_start = time.time()
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            request_time = time.time() - request_start
                            results.append({
                                'success': True,
                                'status': response.status,
                                'duration': request_time,
                                'timestamp': time.time()
                            })
                    except Exception as e:
                        results.append({
                            'success': False,
                            'error': str(e),
                            'duration': time.time() - request_start,
                            'timestamp': time.time()
                        })
                    
                    # Small delay between requests
                    await asyncio.sleep(0.1)
                    
        # Run concurrent users
        tasks = [make_request() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)
        
        # Analyze results
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        durations = [r['duration'] for r in successful]
        
        analysis = {
            'endpoint': endpoint,
            'concurrent_users': concurrent_users,
            'duration_seconds': duration_seconds,
            'total_requests': len(results),
            'successful_requests': len(successful),
            'failed_requests': len(failed),
            'requests_per_second': len(results) / duration_seconds,
            'error_rate': (len(failed) / len(results) * 100) if results else 0
        }
        
        if durations:
            analysis.update({
                'min_response_time': min(durations),
                'max_response_time': max(durations),
                'avg_response_time': statistics.mean(durations),
                'median_response_time': statistics.median(durations),
                'p95_response_time': statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else durations[0],
                'p99_response_time': statistics.quantiles(durations, n=100)[98] if len(durations) > 1 else durations[0]
            })
            
        self.test_results.append(analysis)
        return analysis
        
    async def run_stress_test(self, endpoint: str, initial_users: int = 5,
                            max_users: int = 100, step: int = 5,
                            step_duration: int = 30) -> Dict[str, Any]:
        """Run stress test with increasing load"""
        results = []
        breaking_point = None
        
        for users in range(initial_users, max_users + 1, step):
            print(f"Testing with {users} concurrent users...")
            
            result = await self.run_load_test(
                endpoint,
                concurrent_users=users,
                duration_seconds=step_duration
            )
            
            results.append({
                'users': users,
                'rps': result['requests_per_second'],
                'avg_response_time': result.get('avg_response_time', 0),
                'error_rate': result['error_rate']
            })
            
            # Check for breaking point (>10% error rate or >5s response time)
            if (result['error_rate'] > 10 or 
                result.get('avg_response_time', 0) > 5):
                breaking_point = users
                break
                
        return {
            'type': 'stress_test',
            'endpoint': endpoint,
            'results': results,
            'breaking_point': breaking_point,
            'max_sustainable_users': breaking_point - step if breaking_point else max_users
        }
        
    async def run_spike_test(self, endpoint: str, normal_users: int = 10,
                           spike_users: int = 100, spike_duration: int = 30) -> Dict[str, Any]:
        """Test system behavior under sudden traffic spike"""
        results = {
            'type': 'spike_test',
            'endpoint': endpoint,
            'phases': []
        }
        
        # Normal load phase
        print(f"Normal load phase: {normal_users} users")
        normal_result = await self.run_load_test(
            endpoint,
            concurrent_users=normal_users,
            duration_seconds=30
        )
        results['phases'].append({
            'phase': 'normal',
            'users': normal_users,
            'metrics': normal_result
        })
        
        # Spike phase
        print(f"Spike phase: {spike_users} users")
        spike_result = await self.run_load_test(
            endpoint,
            concurrent_users=spike_users,
            duration_seconds=spike_duration
        )
        results['phases'].append({
            'phase': 'spike',
            'users': spike_users,
            'metrics': spike_result
        })
        
        # Recovery phase
        print(f"Recovery phase: {normal_users} users")
        recovery_result = await self.run_load_test(
            endpoint,
            concurrent_users=normal_users,
            duration_seconds=30
        )
        results['phases'].append({
            'phase': 'recovery',
            'users': normal_users,
            'metrics': recovery_result
        })
        
        # Analyze recovery
        normal_response_time = normal_result.get('avg_response_time', 0)
        recovery_response_time = recovery_result.get('avg_response_time', 0)
        
        results['recovery_analysis'] = {
            'recovered': abs(recovery_response_time - normal_response_time) < 0.1,
            'recovery_degradation': (recovery_response_time - normal_response_time) / normal_response_time * 100 if normal_response_time > 0 else 0
        }
        
        return results


class PerformanceDashboard:
    """Performance monitoring dashboard data provider"""
    
    def __init__(self, web_vitals: CoreWebVitalsTracker,
                 realtime: RealTimeMetricsCollector):
        self.web_vitals = web_vitals
        self.realtime = realtime
        
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        return {
            'realtime_metrics': self.realtime.get_current_metrics(),
            'web_vitals': self.web_vitals.get_vitals_summary(),
            'timestamp': datetime.now().isoformat()
        }
        
    def get_performance_score(self) -> Dict[str, Any]:
        """Calculate overall performance score"""
        vitals_summary = self.web_vitals.get_vitals_summary()
        realtime_metrics = self.realtime.get_current_metrics()
        
        # Calculate scores (0-100)
        scores = {
            'web_vitals_score': self._calculate_vitals_score(vitals_summary),
            'response_time_score': self._calculate_response_score(realtime_metrics),
            'availability_score': self._calculate_availability_score(realtime_metrics),
            'error_rate_score': max(0, 100 - realtime_metrics.get('error_rate', 0) * 10)
        }
        
        # Overall score (weighted average)
        overall_score = (
            scores['web_vitals_score'] * 0.4 +
            scores['response_time_score'] * 0.3 +
            scores['availability_score'] * 0.2 +
            scores['error_rate_score'] * 0.1
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'scores': scores,
            'grade': self._get_grade(overall_score),
            'timestamp': datetime.now().isoformat()
        }
        
    def _calculate_vitals_score(self, vitals_summary: Dict) -> float:
        """Calculate web vitals score"""
        if not vitals_summary.get('overall'):
            return 50.0
            
        score = 100.0
        
        # Deduct points for poor metrics
        for metric_name, data in vitals_summary['overall'].items():
            p75 = data.get('p75', 0)
            rating = self.web_vitals.get_rating(metric_name, p75)
            
            if rating == 'needs-improvement':
                score -= 15
            elif rating == 'poor':
                score -= 30
                
        return max(0, score)
        
    def _calculate_response_score(self, metrics: Dict) -> float:
        """Calculate response time score"""
        avg_response = metrics.get('average_response_time', 0)
        
        if avg_response < 0.1:  # < 100ms
            return 100
        elif avg_response < 0.2:  # < 200ms
            return 90
        elif avg_response < 0.5:  # < 500ms
            return 70
        elif avg_response < 1.0:  # < 1s
            return 50
        else:
            return max(0, 100 - (avg_response * 20))
            
    def _calculate_availability_score(self, metrics: Dict) -> float:
        """Calculate availability score based on error rate"""
        error_rate = metrics.get('error_rate', 0)
        
        if error_rate == 0:
            return 100
        elif error_rate < 0.1:  # < 0.1%
            return 99
        elif error_rate < 1:  # < 1%
            return 95
        elif error_rate < 5:  # < 5%
            return 80
        else:
            return max(0, 100 - error_rate * 10)
            
    def _get_grade(self, score: float) -> str:
        """Get letter grade for score"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'