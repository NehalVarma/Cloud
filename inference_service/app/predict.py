import os
import time
import logging
from typing import Dict, Any
from PIL import Image
from .model_loader import ModelLoader

logger = logging.getLogger(__name__)

class PredictionService:
    """Service for handling image predictions."""
    
    def __init__(self):
        self.model_loader = ModelLoader()
        self.server_id = os.getenv('SERVER_ID', f"{os.getenv('HOSTNAME', 'localhost')}:5000")
        self.model_version = os.getenv('MODEL_VERSION', 'v1')
        
    def initialize(self) -> bool:
        """Initialize the prediction service."""
        return self.model_loader.load_model()
        
    def predict_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Predict image classification and return detailed results.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with prediction results
        """
        start_time = time.time()
        
        try:
            # Preprocess image
            processed_image = self.model_loader.preprocess_image(image)
            
            # Make prediction
            label, confidence = self.model_loader.predict(processed_image)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            result = {
                "label": label,
                "confidence": confidence,
                "model_version": self.model_version,
                "server_id": self.server_id,
                "latency_ms": round(latency_ms, 2),
                "timestamp": time.time(),
                "status": "success"
            }
            
            logger.info(f"Prediction completed: {label} ({confidence:.3f}) in {latency_ms:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                "error": str(e),
                "server_id": self.server_id,
                "model_version": self.model_version,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": time.time(),
                "status": "error"
            }
            
    def is_ready(self) -> bool:
        """Check if the service is ready to handle predictions."""
        return self.model_loader.is_loaded()