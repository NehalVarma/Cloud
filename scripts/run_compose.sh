#!/bin/bash

echo "🚀 Starting AI SDN Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build images first
echo "📦 Building Docker images..."
./scripts/build_all.sh

# Start the complete stack
echo "🌟 Starting all services with Docker Compose..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

echo "📊 Frontend: http://localhost:3000"
echo "🤖 Load Balancer API: http://localhost:8080"
echo "📈 Prometheus: http://localhost:9090"
echo "📊 Grafana: http://localhost:3001 (admin/admin123)"

# Test basic connectivity
echo "🧪 Testing basic connectivity..."

# Test inference service directly
if curl -s http://localhost:5001/health > /dev/null; then
    echo "✅ Inference Service 1: OK"
else
    echo "❌ Inference Service 1: Failed"
fi

if curl -s http://localhost:5002/health > /dev/null; then
    echo "✅ Inference Service 2: OK"
else
    echo "❌ Inference Service 2: Failed"
fi

# Test load balancer
if curl -s http://localhost:8080/api/server-stats > /dev/null; then
    echo "✅ Load Balancer: OK"
else
    echo "❌ Load Balancer: Failed"
fi

# Test frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: Failed"
fi

echo ""
echo "🎉 Platform started! Access the web interface at: http://localhost:3000"
echo "📋 To see logs: docker compose logs -f"
echo "🛑 To stop: docker compose down"