import pytest
import requests
import time
import io
import sys
import os
from PIL import Image
import numpy as np

# Test configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5001')

class TestAPISmoke:
    """Smoke tests for the API endpoints."""
    
    @pytest.fixture
    def test_image(self):
        """Create a test image for API calls."""
        # Create a simple test image
        image_array = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        image = Image.fromarray(image_array, 'RGB')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    def test_health_endpoint(self):
        """Test the health endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields
            assert 'status' in data
            assert 'server_id' in data
            assert 'timestamp' in data
            
            if data['status'] == 'healthy':
                assert 'metrics' in data
                metrics = data['metrics']
                assert 'cpu_percent' in metrics
                assert 'memory_percent' in metrics
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_ready_endpoint(self):
        """Test the readiness endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/ready", timeout=10)
            
            # Should be 200 (ready) or 503 (not ready)
            assert response.status_code in [200, 503]
            
            data = response.json()
            assert 'status' in data
            assert 'server_id' in data
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_info_endpoint(self):
        """Test the server info endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/info", timeout=10)
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields
            required_fields = ['server_id', 'model_name', 'model_version', 'port', 'status']
            for field in required_fields:
                assert field in data
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_metrics_endpoint(self):
        """Test the Prometheus metrics endpoint."""
        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=10)
            
            assert response.status_code == 200
            assert response.headers['content-type'] == 'text/plain; charset=utf-8'
            
            # Check for some expected metrics
            content = response.text
            assert 'inference_requests_total' in content
            assert 'inference_latency_seconds' in content
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_predict_endpoint_with_image(self, test_image):
        """Test the prediction endpoint with a real image."""
        try:
            files = {
                'image': ('test_image.jpg', test_image, 'image/jpeg')
            }
            
            response = requests.post(
                f"{API_BASE_URL}/predict", 
                files=files, 
                timeout=30
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required response fields
            if 'error' not in data:
                required_fields = ['label', 'confidence', 'server_id', 'latency_ms', 'model_version']
                for field in required_fields:
                    assert field in data
                    
                # Validate data types and ranges
                assert isinstance(data['label'], str)
                assert 0.0 <= data['confidence'] <= 1.0
                assert isinstance(data['latency_ms'], (int, float))
                assert data['latency_ms'] >= 0
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_predict_endpoint_no_image(self):
        """Test the prediction endpoint without an image."""
        try:
            response = requests.post(f"{API_BASE_URL}/predict", timeout=10)
            
            assert response.status_code == 400
            data = response.json()
            assert 'error' in data
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_predict_endpoint_invalid_file(self):
        """Test the prediction endpoint with invalid file."""
        try:
            files = {
                'image': ('test.txt', b'not an image', 'text/plain')
            }
            
            response = requests.post(
                f"{API_BASE_URL}/predict", 
                files=files, 
                timeout=10
            )
            
            assert response.status_code == 400
            data = response.json()
            assert 'error' in data
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_performance_baseline(self, test_image):
        """Test performance baseline for predictions."""
        try:
            files = {
                'image': ('test_image.jpg', test_image, 'image/jpeg')
            }
            
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/predict", 
                files=files, 
                timeout=30
            )
            end_time = time.time()
            
            request_time = (end_time - start_time) * 1000  # ms
            
            assert response.status_code == 200
            data = response.json()
            
            if 'error' not in data:
                # Performance expectations (adjust based on your requirements)
                assert request_time < 10000  # Less than 10 seconds
                assert data['latency_ms'] < 5000  # Model inference < 5 seconds
                
                print(f"Request time: {request_time:.2f}ms")
                print(f"Model latency: {data['latency_ms']:.2f}ms")
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")
    
    def test_concurrent_requests(self, test_image):
        """Test handling of concurrent requests."""
        import concurrent.futures
        
        def make_request():
            files = {
                'image': ('test_image.jpg', test_image, 'image/jpeg')
            }
            response = requests.post(
                f"{API_BASE_URL}/predict", 
                files=files, 
                timeout=30
            )
            return response.status_code, response.json()
        
        try:
            # Make 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All requests should succeed
            for status_code, data in results:
                assert status_code == 200
                if 'error' not in data:
                    assert 'label' in data
                    assert 'confidence' in data
                    
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not available: {e}")

if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])