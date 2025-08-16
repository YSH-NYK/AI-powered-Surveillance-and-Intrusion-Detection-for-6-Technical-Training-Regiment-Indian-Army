import React, { useEffect, useState } from "react";
import axios from "axios";
import "./Human_Detection.css";

import Navbar from "../Navbar/Navbar";

// Use /human_detection as prefix
const BACKEND_URL = "http://127.0.0.1:5000/human_detection";

const Human_Detection = () => {
  const [images, setImages] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalImage, setModalImage] = useState(null);

  // Fetch all images (read + unread) once on mount
  const fetchAllImages = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/detection_images`);
      setImages(res.data);
    } catch (error) {
      console.error("Failed to fetch all images:", error);
    }
  };

  // Fetch only unread images periodically
  const fetchUnreadImages = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/unread_detection_images`);
      setImages((prevImages) => {
        const existingIds = new Set(prevImages.map((img) => img.id));
        const newUnread = res.data.filter((img) => !existingIds.has(img.id));
        return [...newUnread, ...prevImages].sort(
          (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
        );
      });
    } catch (error) {
      console.error("Failed to fetch unread images:", error);
    }
  };

  // Mark image as read
  const markAsRead = async (id) => {
    try {
      await axios.post(`${BACKEND_URL}/mark_read/${id}`);
      setImages((prevImages) =>
        prevImages.map((img) => (img.id === id ? { ...img, read: true } : img))
      );
    } catch (error) {
      console.error("Failed to mark image as read:", error);
    }
  };

  // Handle image click (open modal)
  const handleImageClick = (img) => {
    if (!img.read) markAsRead(img.id);
    setModalImage(img);
    setModalOpen(true);
  };

  // Handle modal close
  const closeModal = () => {
    setModalOpen(false);
    setModalImage(null);
  };

  // Handle image delete
  const handleDeleteImage = async (id) => {
    if (!window.confirm("Are you sure you want to delete this image?")) return;
    try {
      await axios.delete(`${BACKEND_URL}/delete_detection_image/${id}`);
      setImages((prevImages) => prevImages.filter((img) => img.id !== id));
      setModalOpen(false);
      setModalImage(null);
    } catch (error) {
      alert("Failed to delete image.");
      console.error("Failed to delete image:", error);
    }
  };

  useEffect(() => {
    fetchAllImages();
    const interval = setInterval(fetchUnreadImages, 1000); // Changed from 5000 to 1000 (1 second)
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <Navbar />
      <div className="human-detection-container">
        <h2 className="human-detection-title">Human Detection Images</h2>
        <div className="images-grid">
          {images.map((img) => (
            <div
              key={img.filename}
              onClick={() => handleImageClick(img)}
              className={`image-card ${img.read ? "" : "unread"}`}
              title={img.read ? "Read" : "Unread - Click to mark as read"}
            >
              <img src={`${BACKEND_URL}${img.url}`} alt={img.filename} />
              <div className="image-filename">{img.filename}</div>
              <div className="image-timestamp">
                {img.timestamp
                  ? new Date(img.timestamp).toLocaleString()
                  : "Unknown time"}
              </div>
              {!img.read && <div className="unread-label">Unread</div>}
            </div>
          ))}
        </div>

        {/* Modal Popup - Restructured */}
        {modalOpen && modalImage && (
          <div className="modal-overlay" onClick={closeModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              {/* Modal Header */}
              <div className="modal-header">
                <div className="modal-title-section">
                  <h3 className="modal-title">{modalImage.filename}</h3>
                  <div className={`status-badge ${modalImage.read ? 'read' : 'unread'}`}>
                    {modalImage.read ? (
                      <>
                        <i className="fas fa-check-circle"></i>
                        Read
                      </>
                    ) : (
                      <>
                        <i className="fas fa-exclamation-circle"></i>
                        Unread
                      </>
                    )}
                  </div>
                </div>
                <button className="modal-close" onClick={closeModal}>
                  <i className="fas fa-times"></i>
                </button>
              </div>

              {/* Modal Body */}
              <div className="modal-body">
                <div className="modal-image-section">
                  <img
                    className="modal-full-image"
                    src={`${BACKEND_URL}${modalImage.url}`}
                    alt={modalImage.filename}
                  />
                </div>

                <div className="modal-info-section">
                  <div className="info-grid">
                    <div className="info-item">
                      <div className="info-label">
                        <i className="fas fa-clock"></i>
                        Detected At
                      </div>
                      <div className="info-value">
                        {modalImage.timestamp
                          ? new Date(modalImage.timestamp).toLocaleString()
                          : "Unknown time"}
                      </div>
                    </div>

                    {modalImage.location_id && (
                      <div className="info-item">
                        <div className="info-label">
                          <i className="fas fa-map-marker-alt"></i>
                          Location ID
                        </div>
                        <div className="info-value">{modalImage.location_id}</div>
                      </div>
                    )}

                    <div className="info-item">
                      <div className="info-label">
                        <i className="fas fa-file-image"></i>
                        File Name
                      </div>
                      <div className="info-value">{modalImage.filename}</div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="modal-actions">
                    <button
                      className="action-btn secondary"
                      onClick={closeModal}
                    >
                      <i className="fas fa-arrow-left"></i>
                      Back to Gallery
                    </button>
                    <button
                      className="action-btn danger"
                      onClick={() => handleDeleteImage(modalImage.id)}
                    >
                      <i className="fas fa-trash-alt"></i>
                      Delete Image
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Human_Detection;