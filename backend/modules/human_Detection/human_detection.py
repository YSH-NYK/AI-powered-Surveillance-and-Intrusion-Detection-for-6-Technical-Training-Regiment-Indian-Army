import os
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.binary import Binary
from bson.objectid import ObjectId
import io

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["Smart_Surveillance"]
human_images_collection = db["human_detection_images"]

human_detection_bp = Blueprint("human_detection", __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to handle human detection image uploads
@human_detection_bp.route('/upload_detection', methods=['POST'])
def upload_detection():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    if 'location_id' not in request.form:
        return jsonify({'error': 'Missing location ID'}), 400

    file = request.files['image']
    location_id = request.form['location_id']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        ts = datetime.now()
        filename = secure_filename(f"detection_{ts.strftime('%Y%m%d_%H%M%S_%f')}.jpg")
        image_bytes = file.read()
        
        doc = {
            "filename": filename,
            "timestamp": ts,
            "image_data": Binary(image_bytes),
            "read": False,
            "location_id": location_id
        }
        
        result = human_images_collection.insert_one(doc)
        return jsonify({
            'message': 'Image uploaded successfully',
            'filename': filename,
            'id': str(result.inserted_id),
            'location_id': location_id
        }), 201
        
    return jsonify({'error': 'Invalid file type'}), 400

# Route to list all detection images
@human_detection_bp.route('/detection_images', methods=['GET'])
def list_detection_images():
    images = []
    for doc in human_images_collection.find({}, {"filename": 1, "timestamp": 1, "read": 1, "location_id": 1}):
        images.append({
            'id': str(doc['_id']),
            'filename': doc.get('filename'),
            'timestamp': doc.get('timestamp').isoformat() if doc.get('timestamp') else None,
            'url': f"/detection_images/{doc['_id']}", 
            'read': doc.get('read', True),
            'location_id': doc.get('location_id', 'N/A')
        })
    images.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(images)

# Route to list unread detection images
@human_detection_bp.route('/unread_detection_images', methods=['GET'])
def list_unread_detection_images():
    images = []
    for doc in human_images_collection.find({"read": False}, {"filename": 1, "timestamp": 1, "read": 1, "location_id": 1}):
        images.append({
            'id': str(doc['_id']),
            'filename': doc.get('filename'),
            'timestamp': doc.get('timestamp').isoformat() if doc.get('timestamp') else None,
            'url': f"/detection_images/{doc['_id']}",  
            'read': doc.get('read', False),
            'location_id': doc.get('location_id', 'N/A')
        })
    images.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(images)

# Route to serve detection images
@human_detection_bp.route('/detection_images/<image_id>')
def serve_detection_image(image_id):
    doc = human_images_collection.find_one({"_id": ObjectId(image_id)})
    if doc and 'image_data' in doc:
        return send_file(
            io.BytesIO(doc['image_data']),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=doc.get('filename', 'image.jpg')
        )
    else:
        return jsonify({"error": "Image not found"}), 404

# Route to mark an image as read
@human_detection_bp.route('/mark_read/<image_id>', methods=['POST'])
def mark_image_read(image_id):
    result = human_images_collection.update_one(
        {"_id": ObjectId(image_id)},
        {"$set": {"read": True}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Image not found"}), 404
    return jsonify({"message": "Image marked as read"})

# Route to delete a detection image
@human_detection_bp.route('/delete_detection_image/<image_id>', methods=['DELETE'])
def delete_detection_image(image_id):
    try:
        result = human_images_collection.delete_one({"_id": ObjectId(image_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Image not found"}), 404
        return jsonify({"message": "Image deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
