import pytest
import sys
import os

# Add the controller to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'controller'))

from ryu_utils import LoadBalancer, LoadBalancingAlgorithm, ServerMetrics

class TestLoadBalancer:
    """Test cases for the LoadBalancer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_servers = [
            ('127.0.0.1', 5001),
            ('127.0.0.1', 5002),
            ('127.0.0.1', 5003)
        ]
        self.lb = LoadBalancer(self.test_servers)
        # Stop health monitoring for tests
        self.lb.health_check_interval = 999999
        
    def test_load_balancer_initialization(self):
        """Test load balancer initialization."""
        assert len(self.lb.servers) == 3
        assert self.lb.current_algorithm == LoadBalancingAlgorithm.ROUND_ROBIN
        
        # Check server IDs
        expected_ids = ['127.0.0.1:5001', '127.0.0.1:5002', '127.0.0.1:5003']
        assert list(self.lb.servers.keys()) == expected_ids
        
    def test_round_robin_algorithm(self):
        """Test round-robin load balancing."""
        self.lb.set_algorithm(LoadBalancingAlgorithm.ROUND_ROBIN)
        
        # All servers healthy
        for server in self.lb.servers.values():
            server.healthy = True
            
        # Test round-robin selection
        selections = []
        for i in range(6):  # Two full rounds
            server = self.lb.select_server()
            selections.append(server.server_id)
            
        # Should cycle through servers
        expected = [
            '127.0.0.1:5001', '127.0.0.1:5002', '127.0.0.1:5003',
            '127.0.0.1:5001', '127.0.0.1:5002', '127.0.0.1:5003'
        ]
        assert selections == expected
        
    def test_least_connections_algorithm(self):
        """Test least connections load balancing."""
        self.lb.set_algorithm(LoadBalancingAlgorithm.LEAST_CONNECTIONS)
        
        # Set up servers with different connection counts
        servers = list(self.lb.servers.values())
        servers[0].healthy = True
        servers[0].active_connections = 5
        servers[1].healthy = True
        servers[1].active_connections = 2
        servers[2].healthy = True
        servers[2].active_connections = 8
        
        # Should select server with least connections (server 2)
        selected = self.lb.select_server()
        assert selected.server_id == '127.0.0.1:5002'
        
    def test_latency_weighted_algorithm(self):
        """Test latency-weighted load balancing."""
        self.lb.set_algorithm(LoadBalancingAlgorithm.LATENCY_WEIGHTED)
        
        # Set up servers with different latencies
        servers = list(self.lb.servers.values())
        servers[0].healthy = True
        servers[0].last_latency_ms = 100.0  # Slowest
        servers[1].healthy = True
        servers[1].last_latency_ms = 50.0   # Fastest
        servers[2].healthy = True
        servers[2].last_latency_ms = 75.0   # Middle
        
        # Should prefer server with lowest latency (highest weight)
        selected = self.lb.select_server()
        assert selected.server_id == '127.0.0.1:5002'
        
    def test_weighted_round_robin_algorithm(self):
        """Test weighted round-robin algorithm."""
        self.lb.set_algorithm(LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN)
        
        # Set up servers with different CPU/memory usage
        servers = list(self.lb.servers.values())
        servers[0].healthy = True
        servers[0].cpu_percent = 80.0    # High CPU usage
        servers[0].memory_percent = 70.0
        servers[1].healthy = True
        servers[1].cpu_percent = 30.0    # Low CPU usage (should be preferred)
        servers[1].memory_percent = 40.0
        servers[2].healthy = True
        servers[2].cpu_percent = 60.0    # Medium CPU usage
        servers[2].memory_percent = 50.0
        
        selected = self.lb.select_server()
        # Should select server with best performance (lowest resource usage)
        assert selected.server_id == '127.0.0.1:5002'
        
    def test_unhealthy_server_filtering(self):
        """Test that unhealthy servers are not selected."""
        # Mark first two servers as unhealthy
        servers = list(self.lb.servers.values())
        servers[0].healthy = False
        servers[1].healthy = False
        servers[2].healthy = True
        
        selected = self.lb.select_server()
        assert selected.server_id == '127.0.0.1:5003'
        
    def test_no_healthy_servers(self):
        """Test behavior when no servers are healthy."""
        # Mark all servers as unhealthy
        for server in self.lb.servers.values():
            server.healthy = False
            
        selected = self.lb.select_server()
        assert selected is None
        
    def test_request_recording(self):
        """Test request recording functionality."""
        server_id = '127.0.0.1:5001'
        latency_ms = 123.45
        
        initial_requests = self.lb.servers[server_id].total_requests
        initial_count = self.lb.request_counts.get(server_id, 0)
        
        self.lb.record_request(server_id, latency_ms)
        
        assert self.lb.servers[server_id].last_latency_ms == latency_ms
        assert self.lb.servers[server_id].total_requests == initial_requests + 1
        assert self.lb.request_counts[server_id] == initial_count + 1
        
    def test_get_server_stats(self):
        """Test server statistics generation."""
        stats = self.lb.get_server_stats()
        
        assert 'algorithm' in stats
        assert 'servers' in stats
        assert 'total_requests' in stats
        assert len(stats['servers']) == 3
        
        # Check server data structure
        server_stats = stats['servers'][0]
        required_fields = [
            'server_id', 'ip', 'port', 'healthy', 'request_count',
            'latency_ms', 'cpu_percent', 'memory_percent', 
            'active_connections', 'weight'
        ]
        for field in required_fields:
            assert field in server_stats
            
    def test_algorithm_change(self):
        """Test changing load balancing algorithms."""
        initial_algorithm = self.lb.current_algorithm
        assert initial_algorithm == LoadBalancingAlgorithm.ROUND_ROBIN
        
        self.lb.set_algorithm(LoadBalancingAlgorithm.LEAST_CONNECTIONS)
        assert self.lb.current_algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS
        
        self.lb.set_algorithm(LoadBalancingAlgorithm.LATENCY_WEIGHTED)
        assert self.lb.current_algorithm == LoadBalancingAlgorithm.LATENCY_WEIGHTED
        
    def test_server_metrics_properties(self):
        """Test ServerMetrics properties."""
        server = ServerMetrics('192.168.1.100', 8080)
        
        assert server.server_id == '192.168.1.100:8080'
        assert server.endpoint == 'http://192.168.1.100:8080'
        assert server.healthy is True  # Default value
        assert server.weight == 1.0    # Default value