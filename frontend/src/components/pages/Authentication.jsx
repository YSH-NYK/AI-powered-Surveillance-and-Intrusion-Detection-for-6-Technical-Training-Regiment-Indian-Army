import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./Autentication.css";

import Navbar from "../Navbar/Navbar";

const Authentication = () => {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [idType, setIdType] = useState("aadhar");
  const [cameraPopupOpen, setCameraPopupOpen] = useState(false);
  const [capturedIdImage, setCapturedIdImage] = useState(null);
  const [ocrPopupOpen, setOcrPopupOpen] = useState(false);
  const [ocrData, setOcrData] = useState({ name: "", roll: "" });
  const [proceedToFaceReg, setProceedToFaceReg] = useState(false);
  const [popupOpen, setPopupOpen] = useState(false);
  const [attendancePopupOpen, setAttendancePopupOpen] = useState(false);
  const [registrationResult, setRegistrationResult] = useState({
    userName: "",
    userImages: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [attendanceData, setAttendanceData] = useState([]);
  const [authMode, setAuthMode] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [availableCameras, setAvailableCameras] = useState([]);
  const [selectedCameraId, setSelectedCameraId] = useState("");

  const instructionSteps = [
    "Ensure you are in a well-lit area with minimal background noise",
    "Look directly at the camera",
    "Keep your face centered",
    "Remain still during capture",
    "Avoid wearing hats or sunglasses",
  ];

  useEffect(() => {
    if (proceedToFaceReg && capturedIdImage) {
      if (authMode) {
        handleAuth();
      } else {
        handleRegister();
      }
      setProceedToFaceReg(false);
    }
  }, [proceedToFaceReg, capturedIdImage]);

  // Start camera when popup opens
  useEffect(() => {
    if (cameraPopupOpen) {
      getCameraDevices();
    } else {
      stopCamera();
      // Reset camera selection when popup closes
      setSelectedCameraId("");
      setCameraError(null);
    }

    return () => {
      stopCamera();
    };
  }, [cameraPopupOpen]);

  // Start camera when a different camera is selected
  useEffect(() => {
    if (selectedCameraId && cameraPopupOpen) {
      // Stop current camera before starting new one
      stopCamera();

      const timeoutId = setTimeout(() => {
        // Start camera after a delay to ensure UI updates
        if (cameraPopupOpen && selectedCameraId) {
          startCamera();
        }
      }, 200); // Increased delay

      // Cleanup function to clear timeout if component unmounts or dependencies change
      return () => {
        clearTimeout(timeoutId);
      };
    }
  }, [selectedCameraId, cameraPopupOpen]);

  const getCameraDevices = async () => {
    try {
      // Stop any existing camera stream first
      stopCamera();

      // Request temporary access to the camera to trigger permissions
      const tempStream = await navigator.mediaDevices.getUserMedia({
        video: true,
      });
      // Stop the temp stream immediately
      tempStream.getTracks().forEach((track) => track.stop());

      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(
        (device) => device.kind === "videoinput"
      );

      setAvailableCameras(videoDevices);

      // Prioritize built-in camera (usually has 'integrated', 'built-in', or is the first device)
      let defaultCamera = null;

      // Look for built-in camera indicators
      const builtInCamera = videoDevices.find(
        (device) =>
          device.label.toLowerCase().includes("integrated") ||
          device.label.toLowerCase().includes("built-in") ||
          device.label.toLowerCase().includes("facetime") ||
          device.label.toLowerCase().includes("internal") ||
          (!device.label.toLowerCase().includes("usb") &&
            !device.label.toLowerCase().includes("external"))
      );

      if (builtInCamera) {
        defaultCamera = builtInCamera;
      } else if (videoDevices.length > 0) {
        // If no clear built-in camera found, use the first one
        defaultCamera = videoDevices[0];
      }

      if (defaultCamera) {
        setSelectedCameraId(defaultCamera.deviceId);
      }
    } catch (error) {
      console.error("Error getting camera devices:", error);
      setCameraError(
        "Failed to access camera devices. Please grant camera permissions."
      );
    }
  };

  const startCamera = async () => {
    try {
      setCameraError(null);

      if (!selectedCameraId) {
        setCameraError("No camera selected");
        return;
      }

      // Stop any existing stream first
      stopCamera();

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          deviceId: { exact: selectedCameraId },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      });

      setCameraStream(stream);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (error) {
      console.error("Error accessing camera:", error);
      setCameraError(
        "Failed to access selected camera. Please try a different camera or check connections."
      );
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => {
        track.stop();
      });
      setCameraStream(null);
    }

    // Also stop video element and clear its source
    if (videoRef.current) {
      videoRef.current.srcObject = null;
      // Pause the video element as well
      videoRef.current.pause();
    }
  };

  const captureImage = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert canvas to base64 image
      const base64Image = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];

      return base64Image;
    }
    return null;
  };

  const handleCaptureID = async () => {
    try {
      const base64Image = captureImage();

      if (!base64Image) {
        window.alert("Failed to capture image. Please try again.");
        return;
      }

      setCapturedIdImage(base64Image);
      setCameraPopupOpen(false); // This will trigger stopCamera via useEffect
      handleOCR(base64Image);
    } catch (error) {
      console.error("Error capturing ID card:", error);
      window.alert("Failed to capture ID card. Please try again.");
    }
  };

  const handleCameraPopupClose = () => {
    // Stop camera first, then close popup
    stopCamera();
    setCameraPopupOpen(false);
    // Clear selected camera to prevent any delayed startCamera calls
    setSelectedCameraId("");
    setCameraError(null);
  };

  const handleOCR = async (image) => {
    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/face_recog/extract-id",
        {
          id_type: idType,
          id_image: image,
        }
      );

      if (response.data.success && response.data.name && response.data.roll) {
        // OCR extraction successful - set the data
        setOcrData({
          name: response.data.name,
          roll: response.data.roll,
        });
      } else {
        // OCR extraction failed or returned empty data - show empty fields
        console.log("OCR extraction failed or returned empty data");
        setOcrData({ name: "", roll: "" });
      }
    } catch (error) {
      // Network error or server error - show empty fields
      console.error("Error extracting OCR data:", error);
      setOcrData({ name: "", roll: "" });
    }

    // Always show the verification popup regardless of OCR success/failure
    setOcrPopupOpen(true);
  };

  const handleRegister = async () => {
    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/face_recog/register-face",
        {
          id_type: idType,
          name: ocrData.name,
          roll: ocrData.roll,
        }
      );

      if (response.data.success) {
        setRegistrationResult({
          userName: response.data.userName,
          userImages: response.data.userImages,
        });
        setPopupOpen(true);
      } else {
        window.alert(response.data.message || "Registration failed");
      }
    } catch (error) {
      console.error("Error sending data:", error);
      window.alert("Registration failed due to a server error");
    }
  };

  const handleAuth = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(
        "http://127.0.0.1:5000/face_recog/Authenticate",
        {
          id_type: idType,
          name: ocrData.name,
          roll: ocrData.roll,
        }
      );

      if (response.data.success) {
        window.alert(
          `${response.data.status}, It's ${response.data.name}_${response.data.roll}`
        );
      } else {
        window.alert(response.data.message || "Authentication failed");
      }
    } catch (error) {
      console.error("Authentication error:", error);
      window.alert("Authentication failed due to a server error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGroupAuth = () => {
    navigate("/group_auth");
  };

  const fetchTodaysAttendance = async () => {
    try {
      const response = await axios.get(
        "http://127.0.0.1:5000/face_recog/todayattendance"
      );

      if (response.data.success) {
        setAttendanceData(response.data.attendance);
        setAttendancePopupOpen(true);
      } else {
        window.alert("No attendance records found");
      }
    } catch (error) {
      console.error("Error fetching attendance:", error);
      window.alert("Failed to fetch attendance");
    }
  };

  const handleGoBack = () => navigate(-1);
  const handleGoHome = () => navigate("/");

  return (
    <div>
      <Navbar />
      <div className="auth-root">
        <div className="auth-id-card-container">
          <div className="auth-navigation-buttons">
            <button onClick={handleGoBack} className="auth-back-btn">
              ◀
            </button>
            <button onClick={handleGoHome} className="auth-home-btn">
              🏠︎
            </button>
          </div>

          <h2 className="auth-title">AUTHENTICATION PROCESS</h2>

          <div className="auth-instructions-box">
            <h3 className="auth-subtitle">Important Instructions</h3>
            <ol className="auth-instruction-list">
              {instructionSteps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ol>
          </div>

          <div className="auth-button-container">
            <button
              className="auth-register-btn"
              onClick={() => {
                setAuthMode(false);
                setCameraPopupOpen(true);
              }}
            >
              Register
            </button>
            <button
              className="auth-authenticate-btn"
              onClick={() => {
                setAuthMode(true);
                setCameraPopupOpen(true);
              }}
              disabled={isLoading}
            >
              {isLoading ? "Authenticating..." : "Authenticate"}
            </button>
            <button className="auth-authenticate-btn" onClick={handleGroupAuth}>
              Group Authentication
            </button>
            <button
              className="auth-attendance-btn"
              onClick={fetchTodaysAttendance}
            >
              Today's Records
            </button>
          </div>
        </div>

        {/* Registration Popup */}
        {popupOpen && (
          <div className="auth-popup-overlay">
            <div className="auth-popup-content">
              <h2>Face Registration Complete</h2>
              <p>
                <strong>{registrationResult.userName}</strong> has been
                successfully registered in the facial recognition system.
              </p>
              <p>
                Your facial features have been analyzed and securely stored as
                encrypted biometric data 
              </p>
              <p className="auth-security-note">
                <em>
                  Note: Only facial feature patterns are stored, not actual
                  images. This ensures your privacy and security.
                </em>
              </p>
              <button onClick={() => setPopupOpen(false)}>Close</button>
            </div>
          </div>
        )}

        {/* Attendance Popup */}
        {attendancePopupOpen && (
          <div className="auth-popup-overlay">
            <div className="auth-popup-content auth-attendance-popup">
              <div className="auth-popup-header">
                <h2>Today's Attendance</h2>
                <button onClick={() => setAttendancePopupOpen(false)}>×</button>
              </div>
              <table className="auth-attendance-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>UID</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceData.map((record, index) => (
                    <tr key={index}>
                      <td>{record[0]}</td>
                      <td>{record[1]}</td>
                      <td>{record[2]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Camera Popup */}
        {cameraPopupOpen && (
          <div className="auth-popup-overlay">
            <div className="auth-popup-content">
              <h2>Select ID Type and Capture ID Card</h2>
              <div className="auth-id-selection-box">
                <label htmlFor="idType" className="auth-id-label">
                  Select ID Type:
                </label>
                <select
                  id="idType"
                  value={idType}
                  onChange={(e) => setIdType(e.target.value)}
                  className="auth-id-select"
                >
                  <option value="aadhar">Aadhar Card</option>
                  <option value="license">Driving License</option>
                  <option value="college">College ID</option>
                </select>
              </div>

              <div className="auth-id-selection-box">
                <label htmlFor="cameraSelect" className="auth-id-label">
                  Select Camera:
                </label>
                <select
                  id="cameraSelect"
                  value={selectedCameraId}
                  onChange={(e) => setSelectedCameraId(e.target.value)}
                  className="auth-id-select"
                >
                  {availableCameras.map((camera, index) => (
                    <option key={camera.deviceId} value={camera.deviceId}>
                      {camera.label || `Camera ${index + 1}`}
                      {index === 0 && availableCameras.length > 1
                        ? " (Default)"
                        : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div className="auth-webcam-container">
                {cameraError ? (
                  <div className="auth-camera-error">
                    <p>{cameraError}</p>
                    <button onClick={getCameraDevices}>Refresh Cameras</button>
                  </div>
                ) : (
                  <video
                    ref={videoRef}
                    className="auth-webcam-feed"
                    autoPlay
                    playsInline
                    muted
                  />
                )}
                <canvas ref={canvasRef} style={{ display: "none" }} />
              </div>

              <div className="auth-popup-actions">
                <button
                  onClick={handleCaptureID}
                  disabled={!cameraStream || cameraError}
                >
                  Capture ID Card
                </button>
                <button onClick={handleCameraPopupClose}>Cancel</button>
              </div>
            </div>
          </div>
        )}

        {/* OCR Verification Popup */}
        {ocrPopupOpen && (
          <div className="auth-popup-overlay">
            <div className="auth-popup-content">
              <h2>Verify Extracted Information</h2>
              <label>Name:</label>
              <input
                type="text"
                value={ocrData.name}
                onChange={(e) =>
                  setOcrData({ ...ocrData, name: e.target.value })
                }
              />
              <label>UID:</label>
              <input
                type="text"
                value={ocrData.roll}
                onChange={(e) =>
                  setOcrData({ ...ocrData, roll: e.target.value })
                }
              />
              <button
                onClick={() => {
                  setOcrPopupOpen(false);
                  setProceedToFaceReg(true);
                }}
              >
                Confirm & {authMode ? "Authenticate" : "Register"}
              </button>
              <button onClick={() => setOcrPopupOpen(false)}>Cancel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Authentication;
