import cv2
import threading
import time
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

class CameraManager:
    """
    Singleton class to manage camera access across different blueprints
    Optimized for USB webcam usage with robust thread safety
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraManager, cls).__new__(cls)
                cls._instance.camera = None
                cls._instance.in_use = False
                cls._instance.camera_index = 0
                cls._instance.last_access = None
                cls._instance.camera_lock = threading.RLock()
                cls._instance.access_timeout = 30
                cls._instance.initialization_attempts = 0
                cls._instance.max_init_attempts = 5
                cls._instance.continuous_use = False
                cls._instance.video_feed_active = False
                cls._instance.video_feed_thread_id = None
                cls._instance.video_feed_lock = threading.Lock()
                cls._instance.cleanup_in_progress = False
            return cls._instance
    
    def set_camera_index(self, index):
        """Configure which camera index to use"""
        with self.camera_lock:
            self.camera_index = index
            if self.camera is not None:
                self.release_camera()
                self.initialization_attempts = 0
    
    def _initialize_usb_camera(self):
        """Initialize USB camera with proper settings and delays"""
        print(f"Initializing USB camera at index {self.camera_index}...")
        
        try:
            camera = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not camera.isOpened():
                camera.release()
                camera = cv2.VideoCapture(self.camera_index)
        except:
            camera = cv2.VideoCapture(self.camera_index)
        
        if not camera.isOpened():
            print(f"Failed to open camera at index {self.camera_index}")
            return None
        
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 15)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        
        time.sleep(2)
        
        successful_reads = 0
        for attempt in range(10):
            ret, frame = camera.read()
            if ret and frame is not None and frame.size > 0:
                successful_reads += 1
                if successful_reads >= 3:
                    break
            time.sleep(0.2)
        
        if successful_reads < 3:
            print(f"Camera opened but not responding properly. Successful reads: {successful_reads}")
            camera.release()
            return None
        
        print(f"USB camera initialized successfully after {attempt + 1} attempts")
        return camera
    
    def get_camera(self):
        """Get camera object with exclusive access - optimized for USB webcam"""
        with self.camera_lock:
            if self.cleanup_in_progress:
                print("Camera cleanup in progress, cannot access camera")
                return None
                
            if self.in_use and not self.continuous_use:
                timeout = self.access_timeout
                start_time = time.time()
                
                while self.in_use and time.time() - start_time < timeout:
                    time.sleep(0.1)
                
                if self.in_use:
                    print("Camera access timeout - camera appears to be in use")
                    self._force_release()
            
            if self.camera is None:
                self.initialization_attempts += 1
                
                if self.initialization_attempts > self.max_init_attempts:
                    print(f"Max initialization attempts ({self.max_init_attempts}) reached")
                    return None
                
                self.camera = self._initialize_usb_camera()
                
                if self.camera is None:
                    print(f"Failed to initialize camera at index {self.camera_index}")
                    time.sleep(1)
                    return None
                
                self.initialization_attempts = 0
            
            if not self.camera.isOpened():
                print("Camera was closed, reinitializing...")
                self.camera = None
                return self.get_camera()
            
            self.in_use = True
            self.last_access = time.time()
            return self.camera
    
    def _force_release(self):
        """Force release camera without lock (internal use only)"""
        if self.camera is not None:
            try:
                self.camera.release()
                time.sleep(0.2)
            except Exception as e:
                print(f"Error force releasing camera: {e}")
            self.camera = None
        self.in_use = False
        self.continuous_use = False
        self.video_feed_active = False
    
    def release_camera(self):
        """Release the camera for other processes to use"""
        with self.camera_lock:
            if self.continuous_use:
                print("Camera in continuous use mode, not releasing")
                return
            
            if self.camera is not None:
                try:
                    self.camera.release()
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Error releasing camera: {e}")
                self.camera = None
            self.in_use = False
    
    def capture_frame(self):
        """Capture a single frame with improved error handling for USB webcam"""
        with self.camera_lock:
            if self.video_feed_active:
                print("Video feed is active, skipping single frame capture to avoid conflicts")
                return False, None
                
            camera = self.get_camera()
            
            if camera is None:
                return False, None
            
            for attempt in range(5):
                try:
                    ret, frame = camera.read()
                    if ret and frame is not None and frame.size > 0:
                        break
                    print(f"Attempt {attempt+1} failed to read valid frame")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"Error reading frame on attempt {attempt+1}: {e}")
                    time.sleep(0.3)
            
            if not self.continuous_use:
                self.release_camera()
            
            if not ret or frame is None or frame.size == 0:
                print("Failed to capture a valid frame after multiple attempts")
                return False, None
                
            return ret, frame
    
    def start_continuous_use(self):
        """Mark camera as being in continuous use (for video feeds)"""
        with self.camera_lock:
            with self.video_feed_lock:
                print("Starting continuous camera use")
                self.continuous_use = True
                self.video_feed_active = True
                self.video_feed_thread_id = threading.current_thread().ident
    
    def stop_continuous_use(self):
        """Stop continuous use and release camera"""
        with self.camera_lock:
            with self.video_feed_lock:
                print("Stopping continuous camera use")
                self.continuous_use = False
                self.video_feed_active = False
                self.video_feed_thread_id = None
                
                if self.camera is not None:
                    try:
                        self.camera.release()
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"Error during stop continuous use: {e}")
                    self.camera = None
                
                self.in_use = False
    
    def is_camera_available(self):
        """Check if camera is available for use"""
        with self.camera_lock:
            return not self.in_use or self.continuous_use
    
    def get_camera_status(self):
        """Get current camera status for debugging"""
        with self.camera_lock:
            with self.video_feed_lock:
                return {
                    "camera_initialized": self.camera is not None,
                    "camera_opened": self.camera.isOpened() if self.camera else False,
                    "in_use": self.in_use,
                    "continuous_use": self.continuous_use,
                    "video_feed_active": self.video_feed_active,
                    "video_feed_thread_id": self.video_feed_thread_id,
                    "camera_index": self.camera_index,
                    "initialization_attempts": self.initialization_attempts,
                    "cleanup_in_progress": self.cleanup_in_progress
                }
    
    def cleanup(self):
        """Clean up camera resources"""
        with self.camera_lock:
            with self.video_feed_lock:
                print("Cleaning up camera resources...")
                self.cleanup_in_progress = True
                
                self.continuous_use = False
                self.video_feed_active = False
                self.video_feed_thread_id = None
                
                if self.camera is not None:
                    try:
                        self.camera.release()
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"Error during cleanup: {e}")
                    self.camera = None
                
                self.in_use = False
                self.initialization_attempts = 0
                self.cleanup_in_progress = False
                print("Camera cleanup completed")

camera_manager = CameraManager()