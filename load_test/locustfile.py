import io
import random
from locust import HttpUser, task, between
from PIL import Image
import numpy as np

class ImageClassificationUser(HttpUser):
    """Locust user for load testing the image classification service."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when the user starts."""
        self.test_images = self._generate_test_images()
        
    def _generate_test_images(self):
        """Generate synthetic test images."""
        images = []
        
        # Generate different types of synthetic images
        for i in range(5):
            # Create a random image
            width, height = 224, 224
            image_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
            
            # Add some patterns to make it more realistic
            if i % 2 == 0:
                # Add horizontal stripes
                for y in range(0, height, 20):
                    image_array[y:y+10] = [255, 0, 0]  # Red stripes
            else:
                # Add vertical stripes
                for x in range(0, width, 20):
                    image_array[:, x:x+10] = [0, 255, 0]  # Green stripes
                    
            # Convert to PIL Image
            image = Image.fromarray(image_array, 'RGB')
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG', quality=85)
            img_bytes.seek(0)
            
            images.append(img_bytes.getvalue())
            
        return images
    
    @task(10)
    def classify_image(self):
        """Main classification task."""
        # Select a random test image
        image_data = random.choice(self.test_images)
        
        # Prepare the file upload
        files = {
            'image': ('test_image.jpg', image_data, 'image/jpeg')
        }
        
        # Make the request
        with self.client.post(
            "/predict",
            files=files,
            catch_response=True,
            name="POST /predict"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if 'label' in result and 'confidence' in result:
                        response.success()
                        # Log some statistics
                        self.environment.events.request.fire(
                            request_type="INFERENCE",
                            name="classification_latency",
                            response_time=result.get('latency_ms', 0),
                            response_length=0,
                            exception=None,
                            context={}
                        )
                    else:
                        response.failure(f"Invalid response format: {result}")
                except Exception as e:
                    response.failure(f"JSON decode error: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Health check task."""
        with self.client.get("/health", name="GET /health") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)
    def server_info(self):
        """Server info task."""
        with self.client.get("/info", name="GET /info") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Server info failed: {response.status_code}")

# Configuration for different scenarios
class LightLoadUser(ImageClassificationUser):
    """Light load user - fewer requests."""
    wait_time = between(3, 8)

class HeavyLoadUser(ImageClassificationUser):
    """Heavy load user - more frequent requests."""
    wait_time = between(0.5, 2)

class BurstLoadUser(ImageClassificationUser):
    """Burst load user - rapid fire requests."""
    wait_time = between(0.1, 0.5)