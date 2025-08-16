import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Group_Auth.css";
import Navbar from "../Navbar/Navbar";

const Group_Auth = () => {
  const navigate = useNavigate();
  const [isPlaying, setIsPlaying] = useState(false);
  const [videoSrc, setVideoSrc] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const startVideoFeed = async () => {
    if (isLoading) return; // Prevent multiple simultaneous calls
    
    setIsLoading(true);
    setError("");
    
    try {
      // First call start_video to prepare the camera
      await axios.post("http://localhost:5000/face_recog/start_video");
      
      // Small delay to ensure camera is ready
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Then set the video source
      setVideoSrc(`http://localhost:5000/face_recog/video_feed?timestamp=${Date.now()}`);
      setIsPlaying(true);
      
    } catch (err) {
      console.error("Error starting video feed:", err);
      setError("Failed to start video feed. Please try again.");
      setIsPlaying(false);
      setVideoSrc("");
    } finally {
      setIsLoading(false);
    }
  };

  const stopVideoFeed = async () => {
    if (isLoading) return; // Prevent multiple simultaneous calls
    
    setIsLoading(true);
    setError("");
    
    try {
      // First clear the video source to stop the stream
      setVideoSrc("");
      setIsPlaying(false);
      
      // Then call the stop endpoint
      await axios.post("http://localhost:5000/face_recog/stop_video");
      
    } catch (err) {
      console.error("Error stopping video feed:", err);
      setError("Failed to stop video feed properly.");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleVideoFeed = () => {
    if (isLoading) return; // Prevent action while loading
    
    if (isPlaying) {
      stopVideoFeed();
    } else {
      startVideoFeed();
    }
  };

  const markAttendance = async () => {
    if (isLoading) return; // Prevent action while loading
    
    setError("");
    
    try {
      const response = await axios.post("http://localhost:5000/face_recog/group_markattendance");
      alert(response.data.message);
    } catch (err) {
      console.error("Error marking attendance:", err);
      setError("Failed to mark attendance. Please try again.");
    }
  };

  // Cleanup on component unmount
  useEffect(() => {
    return () => {
      if (isPlaying) {
        axios.post("http://localhost:5000/face_recog/stop_video")
          .catch(err => console.error("Error stopping video feed on unmount:", err));
      }
    };
  }, [isPlaying]); 

  const handleImageError = (e) => {
    console.error("Video feed image error:", e);
    setError("Video feed connection lost. Please try refreshing.");
  };

  const handleGoBack = () => navigate(-1);
  const handleGoHome = () => navigate("/");

  return (
    <div>
      <Navbar />
      <div className="Group_div">
        <div className="navigation-buttons">
          <button onClick={handleGoBack} className="back-btn">
            ◀
          </button>
          <button onClick={handleGoHome} className="home-btn">
            🏠︎
          </button>
        </div>

        <h1>Group Recognition</h1>

        {/* Error display */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* Status indicator */}
        <div className="status-indicator">
          <div className={`indicator ${isPlaying ? 'active' : 'inactive'}`}></div>
          <span>{isPlaying ? 'Video feed active' : 'Video feed inactive'}</span>
        </div>

        {/* Video feed display */}
        {videoSrc ? (
          <img 
            id="video-feed" 
            src={videoSrc} 
            alt="Live Video Feed" 
            onError={handleImageError}
          />
        ) : (
          <div className="video-loading">
            {isLoading ? 'Starting video feed...' : 'Click "Start Video Feed" to begin recognition.'}
          </div>
        )}

        <div className="button-container">
          <button 
            onClick={markAttendance}
            disabled={isLoading || !isPlaying}
          >
            {isLoading ? 'Loading...' : 'Mark Attendance'}
          </button>
          <button 
            onClick={toggleVideoFeed}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : (isPlaying ? 'Stop Video Feed' : 'Start Video Feed')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Group_Auth;