import os
import logging
from io import BytesIO
from PIL import Image
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .predict import PredictionService
from .health import HealthService
from .metrics_middleware import MetricsMiddleware, get_metrics, record_prediction_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize services
prediction_service = PredictionService()
health_service = HealthService()

# Server configuration
SERVER_ID = os.getenv('SERVER_ID', f"{os.getenv('HOSTNAME', 'localhost')}:5000")
PORT = int(os.getenv('PORT', 5000))

# Initialize metrics middleware
metrics_middleware = MetricsMiddleware(app, SERVER_ID)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancer."""
    health_status = health_service.get_health_status()
    if health_service.is_healthy():
        return jsonify(health_status), 200
    else:
        return jsonify(health_status), 503

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint."""
    if prediction_service.is_ready():
        return jsonify({
            "status": "ready",
            "server_id": SERVER_ID,
            "message": "Service is ready to handle requests"
        }), 200
    else:
        return jsonify({
            "status": "not_ready",
            "server_id": SERVER_ID,
            "message": "Service is not ready"
        }), 503

@app.route('/predict', methods=['POST'])
def predict():
    """Main prediction endpoint."""
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                "error": "No image file provided",
                "server_id": SERVER_ID
            }), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                "error": "No image file selected",
                "server_id": SERVER_ID
            }), 400
            
        # Validate file type
        if not file.content_type.startswith('image/'):
            return jsonify({
                "error": "File is not an image",
                "server_id": SERVER_ID
            }), 400
            
        # Load and process image
        try:
            image = Image.open(BytesIO(file.read()))
        except Exception as e:
            return jsonify({
                "error": f"Invalid image file: {str(e)}",
                "server_id": SERVER_ID
            }), 400
            
        # Make prediction
        result = prediction_service.predict_image(image)
        
        # Record metrics
        if result.get("status") == "success":
            record_prediction_metrics(
                SERVER_ID,
                result.get("model_version", "v1"),
                os.getenv('MODEL_NAME', 'MobileNetV2')
            )
            
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Prediction endpoint error: {e}")
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "server_id": SERVER_ID
        }), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    return Response(get_metrics(), mimetype='text/plain')

@app.route('/info', methods=['GET'])
def server_info():
    """Server information endpoint."""
    return jsonify({
        "server_id": SERVER_ID,
        "model_name": os.getenv('MODEL_NAME', 'MobileNetV2'),
        "model_version": os.getenv('MODEL_VERSION', 'v1'),
        "port": PORT,
        "status": "running"
    })

def create_app():
    """Application factory."""
    # Initialize prediction service
    if not prediction_service.initialize():
        logger.error("Failed to initialize prediction service")
        
    return app

if __name__ == '__main__':
    # Initialize the app
    app = create_app()
    
    logger.info(f"Starting inference server on port {PORT}")
    logger.info(f"Server ID: {SERVER_ID}")
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )