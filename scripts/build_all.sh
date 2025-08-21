#!/bin/bash

# Build all Docker images
echo "🚀 Building all Docker images..."

# Build inference service
echo "📦 Building inference service..."
docker build -t ai-inference-service ./inference_service

# Build controller/load balancer
echo "📦 Building SDN controller..."
docker build -t ai-sdn-controller ./controller

echo "✅ All images built successfully!"

# Verify images
echo "📋 Docker images:"
docker images | grep -E "(ai-inference|ai-sdn)" || echo "No images found"