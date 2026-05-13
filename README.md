# AgriMind-Ethiopia
AI-powered crop disease detection and farmer assistance platform for Ethiopia.
# 🌱 AgriMind Ethiopia

**AI-powered agriculture assistant for Ethiopian farmers**

AgriMind Ethiopia is a smart agricultural platform that helps farmers detect crop diseases, receive AI-based recommendations, and improve productivity using machine learning and computer vision.

---

## 🚀 Features

- 🔐 User Authentication (JWT-based)
- 👨‍🌾 Farmer & Admin roles
- 🌿 AI Crop Disease Detection (Image-based prediction)
- 📊 Prediction history tracking
- 📁 Image upload & storage system
- 🤖 AI recommendation system
- ⚡ FastAPI backend architecture

---

## 🧠 AI System

The system analyzes crop images and predicts diseases such as:

- Tomato Early Blight
- Tomato Late Blight
- Maize Northern Leaf Blight
- Other plant diseases (expandable model)

---

## 🏗️ Tech Stack

**Backend**
- FastAPI
- SQLAlchemy
- SQLite (development stage)
- JWT Authentication
- Passlib (password hashing)

**AI**
- PyTorch / CNN / Vision Transformer (planned upgrade)

**Future Frontend**
- Flutter (Mobile App)

---

## 📡 API Endpoints

### Authentication
- `POST /auth/register` → Register new user
- `POST /auth/login` → Login user

### Users
- `GET /users/me` → Get current user info

### Prediction
- `POST /predict/` → Upload crop image and get disease prediction
- `GET /predict/history` → Get prediction history

---

## 🧪 MVP Status

- Backend API: ✅ Completed
- Authentication: ✅ Completed
- AI Prediction: ✅ Working (demo model)
- Frontend: 🚧 In progress (Flutter planned)

---

## 📦 Installation

```bash
git clone https://github.com/FETHUMOHAMMED/AgriMind-Ethiopia.git
cd AgriMind-Ethiopia
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload


🌍 Vision
To empower Ethiopian farmers with AI-driven tools that improve crop health, reduce losses, and increase productivity.

📌 Future Improvements
🌦️ Weather prediction integration
📱 Flutter mobile app
🌐 Multi-language support (Amharic, Afaan Oromo)
☁️ Cloud deployment (AWS / Railway / Render)
🧠 Better AI model (custom-trained dataset)

👨‍💻 Author

Developed by AgriMind Ethiopia Team

GitHub: https://github.com/FETHUMOHAMMED/AgriMind-Ethiopia