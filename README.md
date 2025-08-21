# AI Image Classification Service with SDN-based Load Balancing

A production-quality AI image classification system with Software-Defined Networking (SDN) based intelligent load balancing, featuring a user-friendly web interface and comprehensive observability.

## 🌟 Features

- **AI Image Classification**: Pre-trained MobileNetV2 model with fallback support
- **SDN Load Balancing**: Ryu controller with multiple algorithms (Round Robin, Least Connections, Latency-weighted)
- **Web Interface**: Drag-and-drop image upload with real-time results and server statistics
- **Observability**: Prometheus metrics and Grafana dashboards
- **Container-ready**: Docker Compose and optional Kubernetes deployment
- **Network Emulation**: Mininet topology for SDN demonstration
- **Health Monitoring**: Automatic failover and health checks
- **Load Testing**: Built-in performance testing with Locust

## 🚀 Quick Start

### Simple Demo (No Docker Required)
1. **Start inference service**: `cd inference_service && pip install flask pillow numpy tensorflow && python -m app.server`
2. **Start web interface**: `cd frontend/static_version && python -m http.server 8000`  
3. **Access**: Open http://localhost:8000 and upload an image!

### Full Docker System
1. **Prerequisites**: Docker, Docker Compose V2
2. **Launch the core services**:
   ```bash
   chmod +x scripts/*.sh
   docker compose up -d inference1 inference2 frontend
   ```
3. **Access the Web UI**: Open http://localhost:3000 in your browser
4. **Upload an image** and see real-time classification results

📖 **For detailed instructions**: See [QUICK_START.md](QUICK_START.md)

## 📁 Project Structure

```
├── inference_service/     # AI classification API service
├── controller/           # Ryu SDN load balancer
├── frontend/            # Web UI (static + optional React)
├── mininet/             # Network topology emulation
├── observability/       # Prometheus & Grafana configs
├── load_test/          # Performance testing scripts
├── k8s/                # Kubernetes deployment manifests
├── scripts/            # Automation scripts
├── tests/              # Unit and integration tests
└── docs/               # Comprehensive documentation
```

## 📖 Documentation

- [**RUN_GUIDE.txt**](docs/RUN_GUIDE.txt) - Detailed setup and usage instructions
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture and design
- [PERFORMANCE_NOTES.md](docs/PERFORMANCE_NOTES.md) - Performance analysis
- [UI_NOTES.md](docs/UI_NOTES.md) - Frontend architecture details

## 🔧 Development

Built with autonomous development principles, including self-healing error recovery and comprehensive testing.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.