// Navbar.jsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

import logo from '../../assets/Logo.png'; 

const Navbar = () => {
  const [showRecordsDropdown, setShowRecordsDropdown] = useState(false);
  const [showServicesDropdown, setShowServicesDropdown] = useState(false);

  const toggleRecordsDropdown = () => {
    setShowRecordsDropdown(!showRecordsDropdown);
    setShowServicesDropdown(false);
  };

  const toggleServicesDropdown = () => {
    setShowServicesDropdown(!showServicesDropdown);
    setShowRecordsDropdown(false);
  };

  const handleBlur = () => {
    setTimeout(() => {
      setShowRecordsDropdown(false);
      setShowServicesDropdown(false);
    }, 150);
  };

  return (
    <div>
      <nav className="navbar">
        <Link to="/" className="logo">
          <img src={logo} alt="SecureVision Logo" className="logo-image" />
          SmartSecure
        </Link>
        <div className="nav-links">
          <Link to="/" className="nav-link">Home</Link>
          
          <div className="dropdown" tabIndex={0} onBlur={handleBlur}>
            <button
              className="dropdown-toggle"
              onClick={toggleRecordsDropdown}
              aria-haspopup="true"
              aria-expanded={showRecordsDropdown}
            >
              Records
              <span className={`dropdown-arrow ${showRecordsDropdown ? 'rotated' : ''}`}>
                <i className="fas fa-chevron-down"></i>
              </span>
            </button>
            {showRecordsDropdown && (
              <div className="dropdown-menu">
                <Link to="/face-records" onClick={() => setShowRecordsDropdown(false)} className="dropdown-item">
                  <i className="fas fa-user-check"></i>
                  Face Recognition
                </Link>
                <Link to="/vehicle-records" onClick={() => setShowRecordsDropdown(false)} className="dropdown-item">
                  <i className="fas fa-car"></i>
                  Vehicle Records
                </Link>
              </div>
            )}
          </div>

          <div className="dropdown" tabIndex={0} onBlur={handleBlur}>
            <button
              className="dropdown-toggle"
              onClick={toggleServicesDropdown}
              aria-haspopup="true"
              aria-expanded={showServicesDropdown}
            >
              Services
              <span className={`dropdown-arrow ${showServicesDropdown ? 'rotated' : ''}`}>
                <i className="fas fa-chevron-down"></i>
              </span>
            </button>
            {showServicesDropdown && (
              <div className="dropdown-menu">
                <Link to="/authentication" onClick={() => setShowServicesDropdown(false)} className="dropdown-item">
                  <i className="fas fa-shield-alt"></i>
                  Authentication
                </Link>
                <Link to="/vehicle" onClick={() => setShowServicesDropdown(false)} className="dropdown-item">
                  <i className="fas fa-search"></i>
                  Vehicle Detect
                </Link>
                <Link to="/human-detection" onClick={() => setShowServicesDropdown(false)} className="dropdown-item">
                  <i className="fas fa-eye"></i>
                  Human Detection
                </Link>
              </div>
            )}
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Navbar;
