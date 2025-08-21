import time
import logging
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from flask import request, g

# Prometheus metrics
REQUEST_COUNT = Counter(
    'inference_requests_total',
    'Total number of inference requests',
    ['method', 'endpoint', 'status', 'server_id']
)

REQUEST_LATENCY = Histogram(
    'inference_latency_seconds',
    'Inference request latency',
    ['endpoint', 'server_id']
)

MODEL_INFO = Gauge(
    'model_version_info',
    'Model version information',
    ['model_name', 'version', 'server_id']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections',
    ['server_id']
)

logger = logging.getLogger(__name__)

class MetricsMiddleware:
    """Middleware for collecting Prometheus metrics."""
    
    def __init__(self, app, server_id: str):
        self.app = app
        self.server_id = server_id
        self.setup_middleware()
        
    def setup_middleware(self):
        """Set up Flask middleware for metrics collection."""
        
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            ACTIVE_CONNECTIONS.labels(server_id=self.server_id).inc()
            
        @self.app.after_request
        def after_request(response):
            # Calculate request latency
            request_latency = time.time() - g.start_time
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code,
                server_id=self.server_id
            ).inc()
            
            REQUEST_LATENCY.labels(
                endpoint=request.endpoint or 'unknown',
                server_id=self.server_id
            ).observe(request_latency)
            
            ACTIVE_CONNECTIONS.labels(server_id=self.server_id).dec()
            
            return response

def record_prediction_metrics(server_id: str, model_version: str, model_name: str):
    """Record model-specific metrics."""
    MODEL_INFO.labels(
        model_name=model_name,
        version=model_version,
        server_id=server_id
    ).set(1)

def get_metrics():
    """Get current Prometheus metrics."""
    return generate_latest()