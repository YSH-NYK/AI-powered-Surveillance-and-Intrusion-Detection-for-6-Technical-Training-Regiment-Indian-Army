from flask import Flask
from flask_cors import CORS
import atexit
import os

# Set OpenMP environment variables to avoid conflicts BEFORE importing any libraries
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from modules.camera_manager.camera_manager import camera_manager
from modules.face_Recognition.face_recognition import face_recognition_bp
from modules.vehicle_identification.vehicle_identification import vehicle_plate_bp
from modules.human_Detection.human_detection import human_detection_bp

app = Flask(__name__)
CORS(app)

# Set camera index to 0 to use USB webcam instead of built-in camera
camera_manager.set_camera_index(0)  

app.register_blueprint(face_recognition_bp, url_prefix='/face_recog')
app.register_blueprint(vehicle_plate_bp, url_prefix='/vehicle_plate')
app.register_blueprint(human_detection_bp, url_prefix='/human_detection')

# Clean up camera resources on application exit
def cleanup_resources():
    print("Cleaning up camera resources...")
    camera_manager.cleanup()

atexit.register(cleanup_resources)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, threaded=True)