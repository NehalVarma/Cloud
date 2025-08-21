import os
import time
import logging
import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from prometheus_client import Counter, Gauge, generate_latest
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ipv4, tcp
from .ryu_utils import LoadBalancer, LoadBalancingAlgorithm

# Prometheus metrics
LB_REQUESTS_TOTAL = Counter(
    'lb_requests_total',
    'Total load balancer requests',
    ['server_id', 'algorithm']
)

LB_SERVER_HEALTH = Gauge(
    'lb_server_health',
    'Server health status (1=healthy, 0=unhealthy)',
    ['server_id']
)

LB_ALGORITHM_CURRENT = Gauge(
    'lb_algorithm_current',
    'Current load balancing algorithm',
    ['algorithm']
)

logger = logging.getLogger(__name__)

class SDNLoadBalancer(app_manager.RyuApp):
    """Ryu-based SDN Load Balancer."""
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    def __init__(self, *args, **kwargs):
        super(SDNLoadBalancer, self).__init__(*args, **kwargs)
        
        # Load balancer configuration
        self.load_balancer = None
        self.virtual_ip = os.getenv('VIRTUAL_IP', '10.0.0.100')
        self.virtual_port = int(os.getenv('VIRTUAL_PORT', 80))
        
        # Initialize servers from environment
        servers = self._parse_servers()
        if servers:
            self.load_balancer = LoadBalancer(servers)
        
        # Start management API
        self.start_management_api()
        
        logger.info("SDN Load Balancer initialized")
        
    def _parse_servers(self):
        """Parse server list from environment variables."""
        servers_env = os.getenv('BACKEND_SERVERS', '')
        if not servers_env:
            # Default servers for development
            return [('127.0.0.1', 5001), ('127.0.0.1', 5002)]
            
        servers = []
        for server_str in servers_env.split(','):
            try:
                ip, port = server_str.strip().split(':')
                servers.append((ip, int(port)))
            except ValueError:
                logger.error(f"Invalid server format: {server_str}")
                
        return servers
        
    def start_management_api(self):
        """Start Flask API for management and stats."""
        self.api_app = Flask(__name__)
        CORS(self.api_app)
        
        @self.api_app.route('/api/server-stats', methods=['GET'])
        def get_server_stats():
            """Get current server statistics."""
            if not self.load_balancer:
                return jsonify({"error": "Load balancer not initialized"}), 500
            return jsonify(self.load_balancer.get_server_stats())
            
        @self.api_app.route('/api/algorithm', methods=['GET', 'POST'])
        def manage_algorithm():
            """Get or set load balancing algorithm."""
            if not self.load_balancer:
                return jsonify({"error": "Load balancer not initialized"}), 500
                
            if request.method == 'GET':
                return jsonify({
                    "algorithm": self.load_balancer.current_algorithm.value
                })
            else:
                try:
                    data = request.get_json()
                    algorithm_name = data.get('algorithm')
                    algorithm = LoadBalancingAlgorithm(algorithm_name)
                    self.load_balancer.set_algorithm(algorithm)
                    
                    # Update Prometheus metric
                    LB_ALGORITHM_CURRENT.labels(algorithm=algorithm_name).set(1)
                    
                    return jsonify({
                        "algorithm": algorithm_name,
                        "status": "updated"
                    })
                except ValueError as e:
                    return jsonify({"error": f"Invalid algorithm: {e}"}), 400
                    
        @self.api_app.route('/api/servers', methods=['GET'])
        def list_servers():
            """List all servers with their status."""
            if not self.load_balancer:
                return jsonify({"error": "Load balancer not initialized"}), 500
                
            servers = []
            for server_id, server in self.load_balancer.servers.items():
                servers.append({
                    "server_id": server_id,
                    "ip": server.ip,
                    "port": server.port,
                    "healthy": server.healthy,
                    "latency_ms": server.last_latency_ms,
                    "cpu_percent": server.cpu_percent,
                    "memory_percent": server.memory_percent
                })
                
            return jsonify({"servers": servers})
            
        @self.api_app.route('/metrics', methods=['GET'])
        def metrics():
            """Prometheus metrics endpoint."""
            # Update server health metrics
            if self.load_balancer:
                for server_id, server in self.load_balancer.servers.items():
                    LB_SERVER_HEALTH.labels(server_id=server_id).set(1 if server.healthy else 0)
                    
            return Response(generate_latest(), mimetype='text/plain')
            
        # Start API server in background thread
        api_port = int(os.getenv('API_PORT', 8080))
        api_thread = threading.Thread(
            target=lambda: self.api_app.run(host='0.0.0.0', port=api_port, debug=False),
            daemon=True
        )
        api_thread.start()
        logger.info(f"Management API started on port {api_port}")
        
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Install default flow (send to controller)
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                         ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)
        
        logger.info(f"Switch {datapath.id} connected")
        
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        """Add a flow entry to the switch."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                   priority=priority, match=match,
                                   instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                   match=match, instructions=inst)
        datapath.send_msg(mod)
        
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle incoming packets."""
        if not self.load_balancer:
            return
            
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        
        # Ignore LLDP packets
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
            
        # Handle IP packets
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip = pkt.get_protocol(ipv4.ipv4)
            if ip and ip.dst == self.virtual_ip:
                # This is a request to our virtual IP
                selected_server = self.load_balancer.select_server()
                
                if selected_server:
                    # Install flow to redirect to selected server
                    self._install_load_balance_flow(
                        datapath, in_port, ip.src, selected_server
                    )
                    
                    # Record request
                    LB_REQUESTS_TOTAL.labels(
                        server_id=selected_server.server_id,
                        algorithm=self.load_balancer.current_algorithm.value
                    ).inc()
                    
                    logger.info(f"Routing request from {ip.src} to {selected_server.server_id}")
                else:
                    logger.warning("No healthy servers available")
                    
        # Forward the packet
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                 in_port=in_port, actions=actions, data=msg.data)
        datapath.send_msg(out)
        
    def _install_load_balance_flow(self, datapath, in_port, client_ip, server):
        """Install flow rules for load balancing."""
        parser = datapath.ofproto_parser
        
        # Forward flow: client -> server
        match_forward = parser.OFPMatch(
            in_port=in_port,
            eth_type=ether_types.ETH_TYPE_IP,
            ipv4_src=client_ip,
            ipv4_dst=self.virtual_ip
        )
        
        actions_forward = [
            parser.OFPActionSetField(ipv4_dst=server.ip),
            parser.OFPActionOutput(2)  # Assume server port is 2
        ]
        
        self.add_flow(datapath, 10, match_forward, actions_forward)
        
        # Return flow: server -> client
        match_return = parser.OFPMatch(
            in_port=2,
            eth_type=ether_types.ETH_TYPE_IP,
            ipv4_src=server.ip,
            ipv4_dst=client_ip
        )
        
        actions_return = [
            parser.OFPActionSetField(ipv4_src=self.virtual_ip),
            parser.OFPActionOutput(in_port)
        ]
        
        self.add_flow(datapath, 10, match_return, actions_return)