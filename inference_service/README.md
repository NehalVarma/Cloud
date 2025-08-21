# AI Image Classification Inference Service

This service provides AI-powered image classification with health monitoring and Prometheus metrics.

## Features

- MobileNetV2-based image classification
- Fallback stub classifier if model fails to load
- Health and readiness checks
- Prometheus metrics collection
- CORS support for web frontend
- Graceful error handling

## API Endpoints

- `POST /predict` - Classify uploaded image
- `GET /health` - Health check with system metrics
- `GET /ready` - Readiness check
- `GET /metrics` - Prometheus metrics
- `GET /info` - Server information

## Environment Variables

- `MODEL_NAME` - Model to use (default: MobileNetV2)
- `MODEL_VERSION` - Model version (default: v1)
- `SERVER_ID` - Server identifier (default: hostname:5000)
- `PORT` - Server port (default: 5000)
- `DEBUG` - Debug mode (default: False)

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m app.server

# Or with Docker
docker build -t inference-service .
docker run -p 5000:5000 inference-service
```