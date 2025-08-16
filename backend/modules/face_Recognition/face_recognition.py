from flask import Blueprint, Response, jsonify, request
import cv2
import faiss
import numpy as np
import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
import threading
import time
import weakref

# Set OpenMP environment variables to avoid conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import dependencies after environment variables are set
from deepface import DeepFace
from modules.face_Recognition.ocr_service import extract_ocr_data
from modules.camera_manager.camera_manager import camera_manager

# MongoDB Connection
from pymongo import MongoClient
from bson.binary import Binary
from bson.objectid import ObjectId
import base64
from io import BytesIO
from PIL import Image

face_recognition_bp = Blueprint("face_recognition", __name__)

MONGO_URI = "mongodb://localhost:27017" 
client = MongoClient(MONGO_URI)
db = client["Smart_Surveillance"]
face_collection = db["face_metadata"]
embeddings_collection = db["face_embeddings"]
attendance_collection = db["User_Logs"]

# Initialize FAISS with 512D embeddings
embedding_dim = 512
faiss_index = faiss.IndexFlatIP(embedding_dim)
embeddings_db = {}

def load_embeddings_from_mongodb():
    """Load stored embeddings from MongoDB into FAISS index"""
    global embeddings_db, faiss_index
    
    # Reset the FAISS index
    faiss_index = faiss.IndexFlatIP(embedding_dim)
    embeddings_db = {}
    
    # Fetch all embeddings from MongoDB
    all_embeddings = list(embeddings_collection.find())
    
    if all_embeddings:
        for embed_doc in all_embeddings:
            user_key = f"{embed_doc['name']}_{embed_doc['face_id']}"
            embedding = np.array(embed_doc['embedding'], dtype=np.float32)
            embeddings_db[user_key] = embedding.tolist()
        
        # Add embeddings to FAISS index
        stored_embeddings = np.array(list(embeddings_db.values()), dtype=np.float32)
        faiss_index.add(stored_embeddings)
    
    print(f"Loaded {len(embeddings_db)} embeddings from MongoDB into FAISS.")

# Load embeddings at startup
load_embeddings_from_mongodb()

# Thread-safe video feed management
video_feed_lock = threading.Lock()
active_video_generators = weakref.WeakSet()  # Track active generators
video_feed_stop_event = threading.Event()

def get_date_today():
    return datetime.now().strftime("%Y-%m-%d")

def save_attendance(name, roll):
    """Save attendance to MongoDB"""
    attendance_collection.insert_one({
        "name": name,
        "roll": roll,
        "timestamp": datetime.now(),
        "date": get_date_today()
    })

def extract_face_embedding(image):
    """Extract face embedding with retry mechanism for reliability"""
    try:
        for attempt in range(3):
            try:
                embedding = DeepFace.represent(image, model_name="ArcFace", enforce_detection=True)[0]["embedding"]
                embedding = np.array(embedding, dtype=np.float32)
                embedding = embedding / np.linalg.norm(embedding)  # Normalize the embedding
                return embedding
            except Exception as e:
                if attempt < 2:  # Try again if not the last attempt
                    print(f"Face embedding extraction attempt {attempt+1} failed: {e}")
                    time.sleep(0.5)
                else:
                    raise e
    except Exception as e:
        print(f"Face embedding extraction error after all attempts: {e}")
        return None

@face_recognition_bp.route("/extract-id", methods=["POST"])
def extract_id():
    """Extract OCR data from ID card image"""
    try:
        data = request.json
        id_type = data.get("id_type")
        id_image_base64 = data.get("id_image")

        # Validate input
        if not id_type or not id_image_base64:
            return jsonify({
                'success': False, 
                'message': 'Missing id_type or id_image'
            })

        # Decode Base64 ID Image
        try:
            img_data = base64.b64decode(id_image_base64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return jsonify({
                    'success': False, 
                    'message': 'Failed to decode image'
                })
                
        except Exception as e:
            return jsonify({
                'success': False, 
                'message': f'Image decoding error: {str(e)}'
            })

        # Extract OCR data
        try:
            ocr_data = extract_ocr_data(frame, id_type)
            
            if not ocr_data or not ocr_data.get("name") or not ocr_data.get("id"):
                return jsonify({
                    'success': False, 
                    'message': 'Failed to extract data from ID card'
                })
                
            new_username = ocr_data["name"]
            new_userid = str(ocr_data["id"])
            
            return jsonify({
                "success": True, 
                "name": new_username, 
                "roll": new_userid
            })
            
        except Exception as e:
            return jsonify({
                'success': False, 
                'message': f'OCR extraction failed: {str(e)}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Server error: {str(e)}'
        })

@face_recognition_bp.route('/register-face', methods=['POST'])
def register_face():
    data = request.json
    new_username = data.get("name", "").upper()  
    new_userid = data.get("roll", "")  
    id_type = data.get("id_type", "")
    
    if not new_username or not new_userid:
        return jsonify({'success': False, 'message': 'Invalid user during face details'})

    # Check if video feed is active before attempting single capture
    camera_status = camera_manager.get_camera_status()
    if camera_status["video_feed_active"]:
        return jsonify({'success': False, 'message': 'Cannot register face while video feed is active. Please stop the video feed first.'})

    # Single frame capture attempt
    ret, frame = camera_manager.capture_frame()
    
    if not ret or frame is None:
        return jsonify({'success': False, 'message': 'Camera error - could not capture frame'})

    # Extract face embedding
    embedding = extract_face_embedding(frame)
    if embedding is None:
        return jsonify({'success': False, 'message': 'No face detected'})

    # Check if user already exists
    user_key = f"{new_username}_{new_userid}"
    if user_key in embeddings_db:
        return jsonify({'success': False, 'message': 'User already registered'})

    # Update FAISS index
    faiss_index.add(np.array([embedding], dtype=np.float32))
    embeddings_db[user_key] = embedding.tolist()
    
    # Store embedding in MongoDB
    embeddings_collection.insert_one({
        "face_id": new_userid,
        "name": new_username,
        "embedding": embedding.tolist(),
        "created_at": datetime.now()
    })

    # Convert Image to Base64 for MongoDB storage
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    img_base64 = base64.b64encode(buffer).decode("utf-8")

    # Save metadata to MongoDB
    face_collection.insert_one({
        "face_id": new_userid,
        "name": new_username,
        "image": img_base64,
        "id_type": id_type
    })

    print(f"Registered {new_username} successfully.")
    return jsonify({'success': True, 'userName': new_username})


@face_recognition_bp.route("/Authenticate", methods=["POST"])
def authenticate():
    data = request.json
    new_username = data.get("name", "")
    new_username = new_username.strip().upper().replace("  ", " ")

    new_userid = data.get("roll", "").strip()
    id_type = data.get("id_type", "")   

    key = f"{new_username}_{new_userid}"
    # Check if the name and roll combination exists in the database
    if key not in embeddings_db:
        return jsonify({"success": False, "message": "User not found"})

    # Check if video feed is active before attempting single capture
    camera_status = camera_manager.get_camera_status()
    if camera_status["video_feed_active"]:
        return jsonify({"success": False, "message": "Cannot authenticate while video feed is active. Please stop the video feed first."})

    # Single frame capture attempt
    ret, frame = camera_manager.capture_frame()
    
    if not ret or frame is None:
        return jsonify({"success": False, "message": "Camera error - could not capture frame"})

    # Extract face embedding
    embedding = extract_face_embedding(frame)
    if embedding is None:
        return jsonify({"success": False, "message": "No face detected"})

    # Check FAISS index size
    if faiss_index.ntotal == 0:
        return jsonify({"success": False, "message": "No registered faces"})

    # Perform FAISS search
    D, I = faiss_index.search(np.array([embedding], dtype=np.float32), k=1)
    
    if D[0][0] > 0.6:  # Threshold for face recognition
        recognized_key = list(embeddings_db.keys())[I[0][0]]
        name, roll = recognized_key.split("_")

        # Save attendance to MongoDB
        save_attendance(name, roll)

        return jsonify({
            "success": True,
            "status": "Face recognized",
            "name": name,
            "roll": roll,
        })

    return jsonify({"success": False, "message": "Face not recognized"})


@face_recognition_bp.route("/todayattendance", methods=["GET"])
def get_todays_attendance():
    try:
        # Get today's start and end date for MongoDB query
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Query MongoDB for today's attendance records
        attendance_records = list(attendance_collection.find({
            "timestamp": {"$gte": today_start, "$lt": today_end}
        }))
        
        if not attendance_records:
            return jsonify({
                "success": False,
                "message": "No attendance records for today"
            })
        
        # Format the attendance records
        formatted_records = []
        for record in attendance_records:
            formatted_records.append([
                record["name"],
                record["roll"],
                record["timestamp"].strftime("%H:%M:%S")
            ])
        
        return jsonify({
            "success": True,
            "attendance": formatted_records
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        })


# Group Recognition Logic
recognized_faces = set()
recognized_faces_lock = threading.Lock()  # Thread-safe access to recognized faces

def generate_video_feed():
    """Robust video feed generator with proper error handling and cleanup"""
    global recognized_faces
    
    print("Starting video feed generation...")
    
    # Get exclusive camera access for video feed
    with video_feed_lock:
        camera_manager.start_continuous_use()
        cap = camera_manager.get_camera()
    
    if cap is None:
        print("Camera not available for video feed")
        camera_manager.stop_continuous_use()
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + 
               b"Camera not available" + b"\r\n")
        return

    # Add this generator to the active set for tracking
    active_video_generators.add(generate_video_feed)
    
    try:
        # Ensure camera settings are optimal for streaming
        cap.set(cv2.CAP_PROP_FPS, 15)  # Lower FPS to reduce processing load
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for real-time feed
    
        frame_skip = 2  # Process every 2nd frame to reduce lag
        frame_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 10
    
        while not video_feed_stop_event.is_set():
            try:
                ret, frame = cap.read()
                if not ret or frame is None:
                    consecutive_failures += 1
                    print(f"Failed to get frame from camera (failure {consecutive_failures})")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        print("Too many consecutive failures, stopping video feed")
                        break
                    
                    time.sleep(0.1)
                    continue
                
                # Reset failure counter on successful frame
                consecutive_failures = 0
                
                frame_count += 1
                if frame_count % frame_skip == 0:
                    try:
                        # Face detection and recognition logic
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
                        for (x, y, w, h) in faces:
                            # Make sure face region is valid
                            if x >= 0 and y >= 0 and x+w <= frame.shape[1] and y+h <= frame.shape[0]:
                                face = frame[y:y+h, x:x+w]
                                
                                # Skip small faces
                                if w < 80 or h < 80:
                                    continue
                                
                                # Extract embedding using existing method
                                embedding = extract_face_embedding(face)
                                if embedding is None:
                                    continue  # Skip if face is not detected properly
        
                                # Perform FAISS search
                                if faiss_index.ntotal > 0:  # Make sure index is not empty
                                    D, I = faiss_index.search(np.array([embedding], dtype=np.float32), k=1)
            
                                    if D[0][0] > 0.5:  # Similarity threshold (adjustable)
                                        recognized_key = list(embeddings_db.keys())[I[0][0]]
                                        name, roll = recognized_key.split("_")
            
                                        # Thread-safe access to recognized faces
                                        with recognized_faces_lock:
                                            recognized_faces.add((name, roll))
                                        
                                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                                        cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                    except Exception as e:
                        print(f"Error processing frame for face recognition: {e}")
        
                # Compress frame for streaming
                ret_encode, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ret_encode:
                    yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + 
                           buffer.tobytes() + b"\r\n")
                else:
                    print("Failed to encode frame")
                    time.sleep(0.1)
            
            except Exception as e:
                print(f"Error in video feed generation loop: {e}")
                time.sleep(0.1)
    
    except Exception as e:
        print(f"Fatal error in video feed generation: {e}")
    
    finally:
        print("Cleaning up video feed resources...")
        # Always clean up, even if an exception occurs
        try:
            camera_manager.stop_continuous_use()
        except Exception as e:
            print(f"Error stopping continuous use: {e}")
        
        # Remove from active generators
        try:
            active_video_generators.discard(generate_video_feed)
        except:
            pass
        
        print("Video feed generation ended")


@face_recognition_bp.route("/video_feed")
def video_feed():
    """Serve video feed with proper error handling"""
    print("Video feed endpoint called")
    
    # Check if camera is available
    camera_status = camera_manager.get_camera_status()
    if camera_status["cleanup_in_progress"]:
        return jsonify({"error": "Camera cleanup in progress"}), 503
    
    # Clear the stop event for new video feed
    video_feed_stop_event.clear()
    
    try:
        return Response(generate_video_feed(), 
                       mimetype="multipart/x-mixed-replace; boundary=frame")
    except Exception as e:
        print(f"Error starting video feed: {e}")
        return jsonify({"error": "Failed to start video feed"}), 500


@face_recognition_bp.route("/stop_video", methods=["POST"])
def stop_video():
    """Stop video feed with proper cleanup"""
    print("Stop video endpoint called")
    
    # Set the stop event to signal all video generators to stop
    video_feed_stop_event.set()
    
    # Give generators time to stop gracefully
    time.sleep(0.5)
    
    # Force cleanup
    try:
        camera_manager.stop_continuous_use()
    except Exception as e:
        print(f"Error during stop_video cleanup: {e}")
    
    # Clear the stop event for next use
    video_feed_stop_event.clear()
    
    return jsonify({"message": "Video feed stopped successfully", "success": True})


@face_recognition_bp.route('/start_video', methods=['POST'])
def start_video():
    """Start video feed (mainly for status - actual feed starts when /video_feed is called)"""
    print("Start video endpoint called")
    
    # Check camera availability
    camera_status = camera_manager.get_camera_status()
    if camera_status["cleanup_in_progress"]:
        return jsonify({"error": "Camera cleanup in progress", "success": False}), 503
    
    # Clear any previous stop events
    video_feed_stop_event.clear()
    
    return jsonify({"message": "Video feed ready to start", "success": True})


@face_recognition_bp.route('/group_markattendance', methods=['POST'])
def group_markattendance():
    """Mark attendance for all recognized faces with thread-safe access"""
    global recognized_faces
    
    with recognized_faces_lock:
        if not recognized_faces:
            return jsonify({"success": False, "message": "No faces recognized."})

        count = len(recognized_faces)
        faces_to_process = recognized_faces.copy()  # Create a copy for processing
        recognized_faces = set()  # Reset the original set
    
    # Process faces outside the lock to avoid blocking
    for name, roll in faces_to_process:
        try:
            save_attendance(name, roll)
        except Exception as e:
            print(f"Error saving attendance for {name} ({roll}): {e}")
    
    return jsonify({
        "success": True, 
        "message": f"Attendance marked for {count} detected faces."
    })


@face_recognition_bp.route('/camera_status', methods=['GET'])
def camera_status():
    """Get camera status for debugging"""
    status = camera_manager.get_camera_status()
    return jsonify(status)

# Dashboard Routes

@face_recognition_bp.route("/records", methods=["GET"])
def get_face_records():
    """Get all face records from database"""
    try:
        # Get all face metadata from MongoDB
        faces = list(face_collection.find())
        
        # Convert ObjectId to string and binary face image to base64
        for face in faces:
            face["_id"] = str(face["_id"])
            if "face_image" in face and face["face_image"]:
                face["face_image"] = base64.b64encode(face["face_image"]).decode("utf-8")
        
        return jsonify(faces), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@face_recognition_bp.route("/stats", methods=["GET"])
def get_face_stats():
    """Get face recognition statistics"""
    try:
        # Get total records
        total_records = face_collection.count_documents({})
        
        # Get attendance today (count unique users who attended today)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        attendance_today = attendance_collection.count_documents({
            "timestamp": {"$gte": today_start, "$lt": today_end}
        })
        
        # Count known faces (where name is not "Unknown")
        known_faces = face_collection.count_documents({
            "name": {"$ne": "Unknown"}
        })
        
        # Only get unknown_faces count if there are actually any unknown faces
        unknown_faces = 0
        if face_collection.count_documents({"name": "Unknown"}) > 0:
            unknown_faces = face_collection.count_documents({
                "name": "Unknown"
            })
        
        stats = {
            "totalRecords": total_records,
            "attendanceToday": attendance_today,
            "knownFaces": known_faces,
            "unknownFaces": unknown_faces
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@face_recognition_bp.route("/attendance/logs", methods=["GET"])
def get_attendance_logs():
    """Get attendance logs with date filtering"""
    try:
        # Get date filter parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates or use defaults
        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            else:
                # Default to today
                start_date = datetime.now().replace(hour=0, minute=0, second=0)
                
            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            else:
                # Default to today end
                end_date = start_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
        # Query MongoDB for attendance logs within date range
        query = {"timestamp": {"$gte": start_date, "$lte": end_date}}
        
        # Get all attendance logs in the date range
        logs = list(attendance_collection.find(query).sort("timestamp", -1))
        
        # Format the logs for the response
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "_id": str(log["_id"]),
                "name": log["name"],
                "roll": log["roll"],
                "timestamp": log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "date": log["date"] if "date" in log else log["timestamp"].strftime("%Y-%m-%d")
            })
        
        return jsonify({
            "success": True,
            "logs": formatted_logs,
            "count": len(formatted_logs)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@face_recognition_bp.route("/delete/<id>", methods=["DELETE"])
def delete_face_record(id):
    """Delete a face record from database"""
    try:
        # Get the face record first
        face_record = face_collection.find_one({"_id": ObjectId(id)})
        if not face_record:
            return jsonify({"error": "Face record not found"}), 404
        
        # Delete from face_collection
        face_collection.delete_one({"_id": ObjectId(id)})
        
        # Also delete from embeddings_collection if it exists
        face_id = face_record.get("face_id")
        name = face_record.get("name")
        
        if face_id and name:
            # Delete from embeddings collection
            embeddings_collection.delete_one({
                "name": name,
                "face_id": face_id
            })
            
            # Reload FAISS index
            load_embeddings_from_mongodb()
        
        return jsonify({"message": "Face record deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@face_recognition_bp.route("/update/<id>", methods=["PUT"])
def update_face_record(id):
    """Update a face record in database"""
    try:
        data = request.json
        
        # Get the current record
        current_record = face_collection.find_one({"_id": ObjectId(id)})
        if not current_record:
            return jsonify({"error": "Face record not found"}), 404
        
        # Update fields
        update_data = {}
        if "name" in data:
            update_data["name"] = data["name"]
        if "id_type" in data:
            update_data["id_type"] = data["id_type"]
        
        # Update in face_collection
        face_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        
        # If name was updated, also update in embeddings_collection
        if "name" in data and current_record.get("face_id"):
            embeddings_collection.update_one(
                {"face_id": current_record["face_id"]},
                {"$set": {"name": data["name"]}}
            )
            
            # Reload FAISS index 
            load_embeddings_from_mongodb()
        
        return jsonify({"message": "Face record updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500