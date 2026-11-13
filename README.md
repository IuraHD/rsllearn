# RSLlingo 🐾

<p align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Animals/Bear.png" alt="Bear" width="120" />
</p>

<p align="center">
  <strong>An Intelligent Learning Platform for Romanian Sign Language (RSL)</strong><br />
  <em>Leveraging Computer Vision, Deep Learning, and Gamified Practice to Support Beginner RSL Learners</em>
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
| **Project Type** | Final Year Dissertation Prototype |
| **Research Area** | Human-Computer Interaction, Computer Vision, Accessibility, and ML-Assisted Learning |

---

## 🌟 Project Overview

**RSLlingo** is a dissertation prototype designed to improve access to Romanian Sign Language learning by combining **computer vision**, **machine learning**, and **gamified educational design**.

Unlike passive video dictionaries or static sign demonstrations, RSLlingo aims to give learners a more interactive practice experience through real-time feedback on sign attempts, lesson progression, and visible performance tracking.

The prototype combines:

- a learner-facing **React** web application
- a **FastAPI** backend for lesson logic, data storage, and AI inference
- a **MediaPipe + OpenCV + TensorFlow** recognition pipeline
- a small self-recorded RSL dataset and an offline training toolkit

### 🚀 Core Pillars

- **Interactive Pedagogy**: A structured lesson flow built around task-based RSL practice.
- **Real-Time Recognition**: Landmark extraction and sequence classification to evaluate sign attempts.
- **Gamified Learning**: XP, streaks, levels, and lesson progress to encourage repeated practice.
- **Dissertation Artefact Focus**: A proof-of-concept system showing how CV-based recognition can support beginner RSL education.

---

## 🛠️ Technology Stack

### Frontend

- **Framework**: `React 19` + `Vite`
- **Typing**: `TypeScript`
- **Styling**: `TailwindCSS v4` + `PostCSS`
- **Vision in Browser**: `@mediapipe/tasks-vision`

### Backend

- **Engine**: `FastAPI`
- **Database**: `SQLite` with `SQLAlchemy ORM`
- **Validation**: `Pydantic`
- **Configuration**: `python-dotenv`

### Dataset & Training Toolkit

- **Data Capture**: `OpenCV` + `MediaPipe`
- **Modeling**: `TensorFlow`
- **Data Processing**: `NumPy`, `pandas`, `scikit-learn`
- **Evaluation Output**: `matplotlib`

---

## 📂 Repository Structure

```text
rsl/
├── backend/                   # FastAPI application server
│   ├── app/                   # Routers, services, schemas, models, and config
│   └── run_backend.bat        # Backend launcher
├── frontend/                  # React single-page application
│   ├── src/                   # Components, screens, hooks, and services
│   ├── package.json
│   └── run_frontend.bat       # Frontend launcher
├── RSLdataset/                # Dataset capture, training, and live-testing tools
│   ├── rsl_data_collector.py
│   ├── rsl_model_trainer.py
│   ├── rsl_testare_live.py
│   └── docs/
├── docs/                      # Supporting project documentation
├── requirements.txt           # Shared Python dependencies for the whole project
├── setup_enviroment.bat       # One-command setup for Python and frontend dependencies
├── start_all.bat              # Unified Windows launcher
├── .env.example               # Example local environment configuration
└── README.md
```

---

## ⚙️ Environment Requirements

### Python

Use **Python 3.10.x**.

This project uses a shared Python environment at the repository root because the dataset toolkit depends on `tensorflow-directml`, which currently requires Python 3.10 for this setup.

### Node.js / npm

Use:

- **Node.js** `20+`
- **npm** `10+`

Validated locally during development:

- Python `3.10.11`
- Node.js `25.2.1`
- npm `11.6.2`

---

## ⚡ Quick Start

### Windows (Recommended)

1. Copy the example environment file:

```bat
copy .env.example .env
```

2. Set up the full project environment:

```bat
setup_enviroment.bat
```

3. Start frontend and backend together:

```bat
start_all.bat
```

Default local URLs:

- **Frontend**: `http://localhost:5173`
- **Backend**: `http://localhost:3001`
- **API Docs**: `http://localhost:3001/docs`

### What `setup_enviroment.bat` does

- checks that Python 3.10 is available
- checks that Node.js and npm are available
- creates or rebuilds the shared root `.venv`
- installs all Python dependencies from `requirements.txt`
- installs frontend dependencies into `frontend/node_modules`

---

## 🧩 Manual Run Options

### Backend

```bat
cd backend
run_backend.bat
```

### Backend Debug Mode

```bat
cd backend
run_backend_debug.bat
```

### Frontend

```bat
cd frontend
run_frontend.bat
```

---

## 🧠 Dataset & Model Workflow

All dataset scripts use the same shared root Python environment.

### Collect Dataset Samples

```bat
cd RSLdataset
run_collector.bat
```

### Train the Model

```bat
cd RSLdataset
run_training.bat
```

### Run Live Testing

```bat
cd RSLdataset
run_testing.bat
```

---

## 📌 Configuration Notes

- The project now uses **one shared Python environment** at the repository root: `.venv`
- Do **not** create separate Python environments inside `backend/` or `RSLdataset/`
- Python dependencies are centralized in the root `requirements.txt`
- The SQLite database path is now **portable across machines** through the root `.env`
- The backend uses a project-relative database location by default: `backend/database/sql_app.db`

---

## 🔐 Prototype Authentication

The current version uses a lightweight prototype identity model:

- user identity is persisted through the `X-User-Id` header
- admin access is controlled through the `ADMIN_EMAIL` environment variable
- the security model is intentionally lightweight because this repository represents a dissertation prototype, not a production deployment

---

## 🧪 Dissertation Scope Notes

- This repository is a **prototype artefact**, not a production-ready platform
- The current dataset and vocabulary are intentionally limited in scope
- The system is designed to demonstrate feasibility, usability direction, and technical integration rather than full RSL coverage
- Future work would include broader datasets, more users, improved feedback granularity, and larger-scale evaluation

---

<p align="center">
  <em>Developed as a dissertation artefact for Romanian Sign Language learning and accessibility research.</em>
</p>

---

## License and reuse

Copyright (c) 2026 Iurie Virlan. **All rights reserved** for the original work
owned by the author. This is a publicly viewable proprietary dissertation
project, not an open-source release.

No broad reuse rights are granted. Uses of the original materials that require
the author's consent require prior written permission, subject to applicable
law and GitHub's applicable Terms of Service, including its viewing and forking
permissions. See [LICENSE](./LICENSE) for the full notice.

Third-party dependencies, models, datasets, media, and other third-party
materials retain their respective licenses and rights; this notice does not
claim ownership of or relicense those materials.
