import time
import threading
import requests
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LoadBalancingAlgorithm(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LATENCY_WEIGHTED = "latency_weighted"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"

@dataclass
class ServerMetrics:
    """Server metrics for load balancing decisions."""
    ip: str
    port: int
    healthy: bool = True
    last_latency_ms: float = 0.0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_connections: int = 0
    total_requests: int = 0
    last_health_check: float = 0.0
    weight: float = 1.0
    
    @property
    def server_id(self) -> str:
        return f"{self.ip}:{self.port}"
    
    @property
    def endpoint(self) -> str:
        return f"http://{self.ip}:{self.port}"

class LoadBalancer:
    """SDN-based load balancer with multiple algorithms."""
    
    def __init__(self, servers: List[Tuple[str, int]]):
        self.servers: Dict[str, ServerMetrics] = {}
        self.current_algorithm = LoadBalancingAlgorithm.ROUND_ROBIN
        self.round_robin_index = 0
        self.health_check_interval = 5  # seconds
        self.request_counts: Dict[str, int] = {}
        
        # Initialize servers
        for ip, port in servers:
            server_id = f"{ip}:{port}"
            self.servers[server_id] = ServerMetrics(ip=ip, port=port)
            self.request_counts[server_id] = 0
            
        # Start health monitoring
        self.health_monitor_thread = threading.Thread(target=self._health_monitor, daemon=True)
        self.health_monitor_thread.start()
        
        logger.info(f"Load balancer initialized with {len(self.servers)} servers")
        
    def set_algorithm(self, algorithm: LoadBalancingAlgorithm):
        """Change the load balancing algorithm."""
        self.current_algorithm = algorithm
        logger.info(f"Load balancing algorithm changed to {algorithm.value}")
        
    def select_server(self) -> Optional[ServerMetrics]:
        """Select the best server based on current algorithm."""
        healthy_servers = [s for s in self.servers.values() if s.healthy]
        
        if not healthy_servers:
            logger.warning("No healthy servers available")
            return None
            
        if self.current_algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin_select(healthy_servers)
        elif self.current_algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_servers)
        elif self.current_algorithm == LoadBalancingAlgorithm.LATENCY_WEIGHTED:
            return self._latency_weighted_select(healthy_servers)
        elif self.current_algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_servers)
        else:
            return healthy_servers[0]  # fallback
            
    def _round_robin_select(self, servers: List[ServerMetrics]) -> ServerMetrics:
        """Round-robin server selection."""
        if not servers:
            return None
        server = servers[self.round_robin_index % len(servers)]
        self.round_robin_index += 1
        return server
        
    def _least_connections_select(self, servers: List[ServerMetrics]) -> ServerMetrics:
        """Select server with least active connections."""
        return min(servers, key=lambda s: s.active_connections)
        
    def _latency_weighted_select(self, servers: List[ServerMetrics]) -> ServerMetrics:
        """Select server based on inverse latency weighting."""
        if not servers:
            return None
            
        # Calculate weights based on inverse latency (lower latency = higher weight)
        for server in servers:
            if server.last_latency_ms > 0:
                server.weight = 1.0 / server.last_latency_ms
            else:
                server.weight = 1.0
                
        # Select based on weights
        total_weight = sum(s.weight for s in servers)
        if total_weight == 0:
            return servers[0]
            
        # Simple weighted selection (can be improved with proper weighted random)
        return max(servers, key=lambda s: s.weight)
        
    def _weighted_round_robin_select(self, servers: List[ServerMetrics]) -> ServerMetrics:
        """Weighted round-robin based on server performance."""
        # For simplicity, use CPU and memory to calculate weights
        for server in servers:
            cpu_weight = max(0.1, 1.0 - (server.cpu_percent / 100.0))
            memory_weight = max(0.1, 1.0 - (server.memory_percent / 100.0))
            server.weight = (cpu_weight + memory_weight) / 2.0
            
        # Select server with highest weight (best performance)
        return max(servers, key=lambda s: s.weight)
        
    def record_request(self, server_id: str, latency_ms: float):
        """Record a completed request for metrics."""
        if server_id in self.servers:
            self.servers[server_id].last_latency_ms = latency_ms
            self.servers[server_id].total_requests += 1
            self.request_counts[server_id] = self.request_counts.get(server_id, 0) + 1
            
    def get_server_stats(self) -> Dict:
        """Get current server statistics for UI."""
        stats = {
            "algorithm": self.current_algorithm.value,
            "servers": [],
            "total_requests": sum(self.request_counts.values())
        }
        
        for server_id, server in self.servers.items():
            stats["servers"].append({
                "server_id": server_id,
                "ip": server.ip,
                "port": server.port,
                "healthy": server.healthy,
                "request_count": self.request_counts.get(server_id, 0),
                "latency_ms": round(server.last_latency_ms, 2),
                "cpu_percent": round(server.cpu_percent, 2),
                "memory_percent": round(server.memory_percent, 2),
                "active_connections": server.active_connections,
                "weight": round(server.weight, 3)
            })
            
        return stats
        
    def _health_monitor(self):
        """Background thread for monitoring server health."""
        while True:
            try:
                for server_id, server in self.servers.items():
                    self._check_server_health(server)
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                time.sleep(1)
                
    def _check_server_health(self, server: ServerMetrics):
        """Check health of a single server."""
        try:
            start_time = time.time()
            response = requests.get(
                f"{server.endpoint}/health",
                timeout=5
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                server.healthy = True
                server.last_latency_ms = latency_ms
                server.last_health_check = time.time()
                
                # Extract metrics from health response
                health_data = response.json()
                metrics = health_data.get("metrics", {})
                server.cpu_percent = metrics.get("cpu_percent", 0.0)
                server.memory_percent = metrics.get("memory_percent", 0.0)
                
                logger.debug(f"Server {server.server_id} healthy (latency: {latency_ms:.2f}ms)")
            else:
                server.healthy = False
                logger.warning(f"Server {server.server_id} unhealthy (status: {response.status_code})")
                
        except Exception as e:
            server.healthy = False
            logger.warning(f"Health check failed for {server.server_id}: {e}")
            
    def get_healthy_servers(self) -> List[ServerMetrics]:
        """Get list of currently healthy servers."""
        return [s for s in self.servers.values() if s.healthy]