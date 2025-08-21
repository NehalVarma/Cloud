import os
import time
import psutil
from typing import Dict, Any

class HealthService:
    """Service for health checks and server metrics."""
    
    def __init__(self):
        self.server_id = os.getenv('SERVER_ID', f"{os.getenv('HOSTNAME', 'localhost')}:5000")
        self.start_time = time.time()
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Uptime
            uptime_seconds = time.time() - self.start_time
            
            return {
                "status": "healthy",
                "server_id": self.server_id,
                "timestamp": time.time(),
                "uptime_seconds": round(uptime_seconds, 2),
                "metrics": {
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(memory.percent, 2),
                    "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                    "disk_percent": round(disk.percent, 2),
                    "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "server_id": self.server_id,
                "timestamp": time.time(),
                "error": str(e)
            }
            
    def is_healthy(self) -> bool:
        """Simple health check for load balancer."""
        try:
            # Check CPU and memory thresholds
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Consider unhealthy if CPU > 90% or memory > 95%
            return cpu_percent < 90 and memory_percent < 95
        except:
            return False