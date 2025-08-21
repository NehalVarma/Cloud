# Quick Start Guide - How to Execute

This guide provides the **simplest way** to get the AI Image Classification Service running.

## Option 1: Simple Web Interface (Recommended for Quick Demo)

### Prerequisites
- Python 3.8+
- Basic image files for testing

### Steps

1. **Start the basic inference service**:
   ```bash
   cd inference_service
   pip install flask pillow numpy flask-cors prometheus-client psutil
   python -m app.server
   ```

2. **In a new terminal, start the web interface**:
   ```bash
   cd frontend/static_version
   python -m http.server 8000
   ```

3. **Access the application**:
   - Open your browser and go to: http://localhost:8000
   - Upload an image and click "Classify Image"
   - View the AI classification results!

## Option 2: Full Docker System (Complete Demo)

### Prerequisites
- Docker
- Docker Compose V2 

### Steps

1. **Clone and enter the repository**:
   ```bash
   git clone <repository-url>
   cd Cloud
   ```

2. **Start the services**:
   ```bash
   # Make scripts executable
   chmod +x scripts/*.sh
   
   # Start just the core services (without complex SDN)
   docker compose up -d inference1 inference2 frontend
   ```

3. **Access the application**:
   - Web Interface: http://localhost:3000
   - Inference API: http://localhost:5001/health (Service 1)
   - Inference API: http://localhost:5002/health (Service 2)

## Option 3: Individual Service Testing

### Test Inference Service Directly
```bash
# Start service
cd inference_service  
pip install -r requirements.txt
python -m app.server

# Test with curl
curl -X POST http://localhost:5000/predict \
  -F "file=@path/to/your/image.jpg"
```

## Troubleshooting

### If Docker builds fail:
- Use Option 1 (Simple Web Interface) instead
- Check that Docker is running: `docker --version`

### If Python packages fail to install:
```bash
pip install --upgrade pip
pip install --trusted-host pypi.org --trusted-host pypi.python.org flask pillow numpy
```

### If web interface doesn't load:
- Check that the server is running on the correct port
- Try a different port: `python -m http.server 8001`

## What You'll See

1. **Upload Interface**: Drag and drop or browse for images
2. **Classification Results**: AI predictions with confidence scores
3. **Server Information**: Which server processed your request
4. **Performance Metrics**: Response time and server load

## Sample Images to Test

Try uploading:
- Photos of cats, dogs, cars
- Nature images
- Everyday objects
- The system uses MobileNetV2 trained on ImageNet

---

**Need the full SDN features?** See [docs/RUN_GUIDE.txt](docs/RUN_GUIDE.txt) for complete setup instructions.