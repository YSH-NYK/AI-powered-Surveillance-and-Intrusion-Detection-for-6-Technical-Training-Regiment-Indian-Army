import React, { createContext, useContext, useEffect, useRef } from "react";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import axios from "axios";
import { useLocation, useNavigate } from "react-router-dom";

const BACKEND_URL = "http://127.0.0.1:5000/human_detection"; // Updated prefix
const POLL_INTERVAL = 1000; // Changed from 3000 to 1000 (1 second)

const ToastContext = createContext();

export const useToast = () => useContext(ToastContext);

export const ToastProvider = ({ children }) => {
  const lastImageRef = useRef(null);
  const location = useLocation();
  const navigate = useNavigate();
  const polling = useRef(null);

  useEffect(() => {
    const poll = async () => {
      try {
        // Updated endpoint: removed /api and added /human_detection prefix
        const res = await axios.get(`${BACKEND_URL}/detection_images`);
        if (res.data && res.data.length > 0) {
          const newest = res.data[0];
          if (lastImageRef.current && newest.filename !== lastImageRef.current.filename) {
            if (!location.pathname.startsWith("/human-detection")) {
              toast.info(
                <span>
                  New human detection image received!{" "}
                  <button
                    onClick={() => {
                      navigate("/human-detection");
                      toast.dismiss();
                    }}
                    style={{
                      marginLeft: 8,
                      color: "blue",
                      textDecoration: "underline",
                      background: "none",
                      border: "none",
                      cursor: "pointer"
                    }}
                  >
                    View
                  </button>
                </span>
              );
            }
          }
          lastImageRef.current = newest;
        }
      } catch (e) {
        // ignore errors
      }
    };

    poll();
    polling.current = setInterval(poll, POLL_INTERVAL);
    return () => clearInterval(polling.current);
  }, [location.pathname]);

  return (
    <ToastContext.Provider value={{}}>
      <ToastContainer position="top-right" autoClose={5000} />
      {children}
    </ToastContext.Provider>
  );
};