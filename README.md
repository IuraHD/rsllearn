# RSLlingo

RSLlingo is a Romanian Sign Language learning platform with:

- a FastAPI backend in `backend/`
- a React + Vite frontend in `frontend/`
- a dataset/training toolkit in `RSLdataset/`

This repository now uses **one shared Python virtual environment** for the whole project:

- shared venv: `C:\Users\IuraHD\Desktop\disertation\rsl\.venv`
- do not create separate virtual environments in `backend/` or `RSLdataset/`

## Version Requirements

### Python

Use **Python 3.10.x** for the shared environment.

Why 3.10:

- the shared `requirements.txt` uses `tensorflow-directml`
- that toolkit currently targets Python 3.10 on this project

Validated locally:

- Python `3.10.11` for the dataset toolkit

### Node.js / npm

Use:

- Node.js `20+`
- npm `10+`

Validated locally:

- Node.js `25.2.1`
- npm `11.6.2`

## Project Layout

```text
rsl/
├── .venv/                     # Shared Python virtual environment
├── backend/                   # FastAPI backend
├── frontend/                  # React + Vite frontend
├── RSLdataset/                # Dataset, training, and live-testing tools
├── requirements.txt           # Shared Python dependencies for the whole repo
├── setup_enviroment.bat       # Sets up Python and frontend dependencies
└── start_all.bat              # Starts backend + frontend on Windows
```

## First-Time Setup

### 1. Set up the full project environment

From the repository root:

```bat
setup_enviroment.bat
```

What it does:

- creates `.venv` with Python 3.10
- upgrades `pip`
- installs all Python dependencies needed by both `backend/` and `RSLdataset/`
- installs frontend npm dependencies in `frontend/node_modules`

## Running the Project

### Option A: Start backend and frontend together

From the repository root:

```bat
start_all.bat
```

Default URLs:

- frontend: `http://localhost:5173`
- backend: `http://localhost:3001`
- backend docs: `http://localhost:3001/docs`

### Option B: Start each part manually

#### Backend

```bat
cd backend
run_backend.bat
```

Debug mode:

```bat
cd backend
run_backend_debug.bat
```

#### Frontend

```bat
cd frontend
run_frontend.bat
```

## Running the Dataset Toolkit

All dataset scripts now use the same shared root `.venv`.

### Data collection

```bat
cd RSLdataset
run_collector.bat
```

### Training

```bat
cd RSLdataset
run_training.bat
```

### Live testing

```bat
cd RSLdataset
run_testing.bat
```

## Manual Python Commands

If you prefer to work directly in the shared environment:

```bat
.\.venv\Scripts\activate
```

Then you can run:

```bat
python -m uvicorn backend.app.main:app --reload --port 3001
```

or:

```bat
cd RSLdataset
python rsl_model_trainer.py
```

## Python Dependencies

Install all Python dependencies with:

```bat
pip install -r requirements.txt
```

This includes:

- backend packages: FastAPI, SQLAlchemy, Pydantic, Uvicorn, python-dotenv
- AI/dataset packages: TensorFlow CPU, TensorFlow DirectML plugin, NumPy, OpenCV, MediaPipe, scikit-learn, pandas, matplotlib

Frontend dependencies are installed by the same setup command:

```bat
setup_enviroment.bat
```

## Environment Variables

Root environment files:

- `.env`
- `.env.example`

Current prototype note:

- admin access is controlled with `ADMIN_EMAIL`
- user identity in the app is still prototype-level and header-based via `X-User-Id`

## Important Notes

- The whole repository should use only the root `.venv`.
- `frontend/node_modules/` is local install output and should not be committed.
- `RSLdataset/dataset/` and saved models are part of the project data footprint and are intentionally kept separate from dependency folders.
- There is a single shared Python dependency file at the repo root: `requirements.txt`.
- If `.venv` was created with a different Python version before, rerun `setup_enviroment.bat` to rebuild it with Python 3.10.
