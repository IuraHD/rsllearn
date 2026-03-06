# RSLlingo 🐾

<p align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Animals/Bear.png" alt="Bear" width="120" />
</p>

<p align="center">
  <strong>An Intelligent Learning Platform for Romanian Sign Language (RSL)</strong><br />
  <em>Leveraging Computer Vision & Deep Learning to Bridge Communication Gaps</em>
</p>

<p align="center">
  <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=000" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=fff" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=fff" />
  <img alt="TensorFlow" src="https://img.shields.io/badge/TensorFlow-2-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=fff" />
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=fff" />
</p>

---

## 🎓 Dissertation Profile

| Field | Details |
| :--- | :--- |
| **Author** | **Iurie Virlan** |
| **Institution** | **Arden University** |
| **Student ID** | **STU171970** |
| **Project Type** | Final Year Dissertation (Prototype) |
| **Research Area** | Human-Computer Interaction & ML-Assisted Learning |

---

## 🌟 Project Overview

**RSLlingo** is a comprehensive educational ecosystem designed to democratize access to Romanian Sign Language. Unlike traditional video-based platforms, RSLlingo uses real-time **MediaPipe landmark extraction** and **Keras/TensorFlow inference** to provide instant feedback on the user's signing accuracy.

### 🚀 Core Pillars
- **Interactive Pedagogy**: A structured learning path with 4 canonical task types:
  - `REPEAT_SIGN`: Shadowing signs with real-time AI validation.
  - `TEXT_TO_SIGN`: Testing production skills from written prompts.
  - `SIGN_TO_TEXT`: Decoding video gestures into meaning.
  - `VIDEO_MULTIPLE_CHOICE`: Recognizing subtle variations in sign production.
- **Advanced Gamification**: XP-based progression, daily streaks, level-ups, and a dynamic leaderboard to sustain engagement.
- **Embedded AI**: Server-side classification of high-dimensional landmark sequences (90 frames x 429 features).
- **Mascot System**: An animated companion that "patrols" and encourages users throughout their learning journey.

---

## 🛠️ Technology Stack

### Frontend
- **Framework**: `React 19` + `Vite`
- **Typing**: `TypeScript`
- **Styling**: `TailwindCSS v4` + `PostCSS`
- **Vision**: `@mediapipe/tasks-vision` (On-device landmark tracking)

### Backend
- **Engine**: `FastAPI` (Python)
- **Database**: `SQLite` with `SQLAlchemy ORM`
- **ML Inference**: `TensorFlow` / `Keras`
- **Validation**: `Pydantic`

### Dataset & Training (Toolkit)
- **Data Capture**: Custom OpenCV/MediaPipe bridge for recording high-fidelity landmark datasets.
- **Architecture**: LSTM/Transformer-based neural networks for sequence classification.

---

## 📂 Repository Structure

```text
rsl/
├── backend/                # FastAPI Application Server
│   ├── app/                # Logic, Routers, DB Models, and Services
│   ├── tests/              # Test suite & Seeding utilities
│   └── requirements.txt    # Backend dependencies
├── frontend/               # React Application (SPA)
│   ├── src/                
│   │   ├── components/     # UI Design System & Mascot logic
│   │   ├── screens/        # Main App Views (Learn, Admin, Profile)
│   │   └── services/       # API abstraction layer
│   └── package.json        
├── RSLdataset/             # Machine Learning Pipeline
│   ├── rsl_data_collector.py  # Dataset gathering tool
│   ├── rsl_model_trainer.py   # Training script
│   └── rsl_testare_live.py    # Desktop live verification
└── start_all.bat           # Unified Windows launcher
```

---

## ⚡ Quick Start

### Windows (Automated)
Simply run the root batch file to spin up both the frontend and backend:
```bash
start_all.bat
```

### Manual Configuration
1. **Prepare Backend**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # .\.venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. **Prepare Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🔐 Prototype Authentication
The current version uses a prototype header-based identity persistence (`X-User-Id`). Admin features are strictly gated by the `ADMIN_EMAIL` environment variable.

---

<p align="center">
  <em>Developed with ❤️ by Iurie Virlan for the RSL Community.</em>
</p>
