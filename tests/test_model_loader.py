import pytest
import sys
import os
from io import BytesIO
from PIL import Image
import numpy as np

# Add the inference service to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'inference_service'))

from app.model_loader import ModelLoader

class TestModelLoader:
    """Test cases for the ModelLoader class."""
    
    def test_model_loader_initialization(self):
        """Test model loader initialization."""
        loader = ModelLoader()
        assert loader.model_version == "v1"
        assert loader.model_name == "MobileNetV2"
        assert not loader.use_fallback
        
    def test_fallback_classifier_initialization(self):
        """Test fallback classifier initialization."""
        loader = ModelLoader()
        loader._init_fallback_classifier()
        
        assert len(loader.fallback_labels) > 0
        assert "cat" in loader.fallback_labels
        assert "dog" in loader.fallback_labels
        
    def test_image_preprocessing(self):
        """Test image preprocessing."""
        loader = ModelLoader()
        
        # Create a test image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # Test normal preprocessing (should resize to 224x224)
        processed = loader.preprocess_image(test_image)
        assert processed.shape == (224, 224, 3)
        
        # Test fallback preprocessing
        loader.use_fallback = True
        processed_fallback = loader.preprocess_image(test_image)
        assert processed_fallback.shape == (224, 224, 3)
        
    def test_fallback_prediction(self):
        """Test fallback prediction mechanism."""
        loader = ModelLoader()
        loader._init_fallback_classifier()
        
        # Create dummy image array
        image_array = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        
        label, confidence = loader._fallback_predict(image_array)
        
        assert isinstance(label, str)
        assert 0.6 <= confidence <= 0.99
        assert label in loader.fallback_labels
        
    def test_model_loading_fallback(self):
        """Test that model loading gracefully falls back on failure."""
        loader = ModelLoader()
        
        # Force fallback by setting an invalid model name
        loader.model_name = "InvalidModel"
        
        # This should succeed by falling back to stub classifier
        result = loader.load_model()
        assert result is True
        assert loader.use_fallback is True
        
    def test_is_loaded_check(self):
        """Test the is_loaded method."""
        loader = ModelLoader()
        
        # Initially not loaded
        assert not loader.is_loaded()
        
        # After fallback initialization
        loader.use_fallback = True
        loader._init_fallback_classifier()
        assert loader.is_loaded()
        
    def test_deterministic_fallback(self):
        """Test that fallback predictions are deterministic for same input."""
        loader = ModelLoader()
        loader._init_fallback_classifier()
        
        # Same input should produce same output
        image_array = np.ones((224, 224, 3), dtype=np.uint8) * 128
        
        label1, confidence1 = loader._fallback_predict(image_array)
        label2, confidence2 = loader._fallback_predict(image_array)
        
        assert label1 == label2
        assert confidence1 == confidence2