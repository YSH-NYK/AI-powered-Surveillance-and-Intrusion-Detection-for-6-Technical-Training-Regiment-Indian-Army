# AI-powered-Surveillance-and-Intrusion-Detection-for-6-Technical-Training-Regiment-Indian-Army 

## 📌 Project Overview  
This is an AI-powered Survelliance and Intrusion detection system built using **React (Frontend)** and **Flask (Backend)**.  
It leverages deep learning models for face detection/recognition and integrates with multiple AI/ML frameworks for scalable and secure identity verification.  

---

## 🚀 Features  
- 🔍 **Real-time Face Recognition** using DeepFace & OpenCV  
- 🖼️ **OCR Support** with Tesseract & PaddleOCR  
- 📦 **AI/ML Models** integrated via TensorFlow, PyTorch & FAISS  
- 🗄️ **Database Support** with MongoDB  
- 🌐 **Frontend** built in **React.js**  
- ⚡ **Backend** powered by **Flask** with REST APIs  
- 🔒 **Scalable Deployment** with Gunicorn & CORS enabled  

---

## 🛠️ Tech Stack  

### Frontend  
- React.js  
- Tailwind / CSS / Shadcn (if used)  
- Axios (for API calls)  

### Backend  
- Flask & Flask-CORS  
- OpenCV (Image Processing)  
- DeepFace (Face Recognition)  
- TensorFlow + Keras  
- PyTorch, torchvision, torchaudio  
- PaddleOCR & PaddlePaddle  
- FAISS + Milvus for vector search  
- MongoDB (pymongo)  
- Gunicorn (for production server)  

---

## ⚙️ Installation  

### 🔹 Frontend Setup  
```bash
# Open terminal in project root
cd frontend

# Install dependencies
npm install

# Start frontend
npm start
```

### 🔹 Backend Setup  
```bash
# Open new terminal
cd frontend/src/backend

# Create virtual environment
python -m venv myenv

# Activate virtual environment (Windows)
myenv\Scripts\activate

# Install required libraries
pip install Flask opencv-python numpy pandas joblib deepface tf-keras
pip install faiss-cpu facenet-pytorch pymilvus torch torchvision gunicorn
pip install pytesseract pymongo[srv] pillow
pip install paddleocr paddlepaddle ultralytics
pip install flask-cors

# Or simply use:
pip install -r requirements.txt

# Run backend
python app.py
```

---

## 📊 Key Modules  
- **Face Recognition** → DeepFace + Facenet-PyTorch  
- **OCR Extraction** → PaddleOCR + Tesseract  
- **Vector Search** → FAISS + Milvus  
- **Database** → MongoDB for user data & logs  
- **Deployment** → Flask APIs + React UI  

---

## 👨‍💻 Authors  
Developed as part of **Final Year Project (Sem 8)** – AI-powered survelliance and Intrustion detection system for 6 Technical Traning Regiment (Indian Army).  
