// Homepage.jsx
import React from 'react';
import './Homepage.css';
import Navbar from '../Navbar/Navbar';

const Homepage = () => {
  const handleAuthenticationClick = () => {
    window.location.href = '/authentication';
  };
     
  const handleVehicleClick = () => {
    window.location.href = '/vehicle';
  };
     
  const handleHumanDetectionClick = () => {
    window.location.href = '/human-detection';
  };

  return (
    <div>
      <Navbar />
             
      {/* Hero Section */}
      <section className="hero" id="home">
        <div className="hero-content">
          <div className="mission-badge">AI AT THE FRONTLINES OF NATIONAL SECURITY</div>
          <h1>AI-Powered Surveillance & Intrusion Detection</h1>
          <p className="hero-subtitle">Advanced military zone protection through real-time face recognition, vehicle authentication, and intelligent intrusion detection systems</p>
          <div className="hero-stats">
            <div className="stat">
              <i className="fas fa-car stat-icon"></i>
              <span className="stat-label">Vehicle Authentication</span>
            </div>
            <div className="stat">
              <i className="fas fa-eye stat-icon"></i>
              <span className="stat-label">Intrusion Detection</span>
            </div>
            <div className="stat">
              <i className="fas fa-user-shield stat-icon"></i>
              <span className="stat-label">Multi-Factor Auth</span>
            </div>
          </div>
          <a href="#services" className="view-services-btn">
            <i className="fas fa-shield-alt"></i>
            EXPLORE DEFENSE SYSTEMS
          </a>
        </div>
        <div className="hero-visual">
          <div className="security-grid">
            <div className="grid-item active"></div>
            <div className="grid-item"></div>
            <div className="grid-item active"></div>
            <div className="grid-item"></div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="services" id="services">
        <div className="services-category">MILITARY DEFENSE SOLUTIONS</div>
        <h2 className="services-title">
          Intelligent surveillance systems engineered for military zone security
        </h2>
        <div className="services-grid">
          <div className="service-card" onClick={handleVehicleClick}>
            <div className="service-icon">
              
              <i className="fas fa-car"></i>
            </div>
            <img
              src="/images/Vehicle_Authentication.jpg"
              alt="Vehicle Authentication System"
            />
            <div className="service-card-content">
              <h3>Vehicle Authentication</h3>
              <p>
                YOLOv8-powered number plate detection with PaddleOCR for automated vehicle verification and access control
              </p>
              <div className="service-tech">
                <span className="tech-tag">YOLOv8</span>
                <span className="tech-tag">PaddleOCR</span>
              </div>
            </div>
          </div>
          
          <div className="service-card" onClick={handleHumanDetectionClick}>
            <div className="service-icon">
              <i className="fas fa-eye"></i>
            </div>
            <img
              src="/images/Intrusion_Detection.jpg"
              alt="Intrusion Detection System"
            />
            <div className="service-card-content">
              <h3>Intrusion Detection</h3>
              <p>Real-time perimeter monitoring with Raspberry Pi deployment, night vision cameras, and Ethernet image transfer</p>
              <div className="service-tech">
                <span className="tech-tag">Raspberry Pi</span>
                <span className="tech-tag">Night Vision</span>
              </div>
            </div>
          </div>
          
          <div className="service-card" onClick={handleAuthenticationClick}>
            <div className="service-icon">
              <i className="fas fa-user-shield"></i>
            </div>
            <img src="/images/2FA.jpg" alt="Face Recognition & ID Verification" />
            <div className="service-card-content">
              <h3>Multi-Factor Authentication</h3>
              <p>DeepFace 512-D embeddings with FAISS indexing for instant identity verification plus Tesseract ID card OCR</p>
              <div className="service-tech">
                <span className="tech-tag">DeepFace</span>
                <span className="tech-tag">FAISS</span>
                <span className="tech-tag">Tesseract</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="mission">
        <div className="mission-content">
          <h2>Defending National Assets</h2>
          <p>Our AI-powered surveillance system represents the next generation of military zone protection, combining cutting-edge computer vision, real-time processing, and intelligent threat detection to safeguard critical infrastructure and personnel.</p>
          <div className="mission-features">
            <div className="feature">
              <i className="fas fa-brain"></i>
              <span>AI-Powered Intelligence</span>
            </div>
            <div className="feature">
              <i className="fas fa-clock"></i>
              <span>Real-Time Processing</span>
            </div>
            <div className="feature">
              <i className="fas fa-lock"></i>
              <span>Military-Grade Security</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Homepage;