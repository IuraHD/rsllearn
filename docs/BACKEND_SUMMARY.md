# Backend Implementation Summary

## 🛠️ Tech Stack
- **Framework**: FastAPI (Asynchronous Python)
- **Database**: SQLite3
- **ORM**: SQLAlchemy
- **Schema Validation**: Pydantic v2
- **ML Inference**: TensorFlow 2.x (Keras `.h5` models)

## 💾 Database Schema
The system uses a relational SQLite database with the following core entities:
1. **User**: Identity and global stats (XP, Level, Streak).
2. **Unit**: High-level groups for lessons.
3. **Lesson**: individual learning modules.
4. **Task**: The atomic unit of learning (Sign, Text, or Video based).
5. **Achievement**: Global badge definitions.
6. **Progress**: Many-to-many relationship tracking user completions with performance metadata (perfect scores, completion date).

## 🔒 Security Model (Prototype)
As this is a dissertation prototype, security is implemented as a "Proof of Concept":
- **Passwords**: Stored with prototype-only plain string comparison. This repo intentionally does not use the previous hashing stack anymore.
- **Session**: Client-side persistence of the `userId`.
- **Identity Integrity**: Middleware checks for the `X-User-Id` header on protected routes.
- **Admin Access**: Hard-coded environment variable check (`ADMIN_EMAIL`) ensures only the designated tester can access the content management system.

## 🧠 AI Inference Logic
The backend acts as a high-performance inference relay:
- **Model Loading**: The Keras model is loaded into memory on startup for zero-latency inference.
- **Data Contract**: Expects a NumPy-compatible array of shape `(90, 429)`.
- **Processing**: The input is normalized, reshaped for the neural network, and passed through the `.predict()` method.
- **Mapping**: The output index is mapped to a human-readable sign label using a `sign_classes.txt` registry.

## 📈 Scalability Considerations
While SQLite is used for the prototype, the implementation uses SQLAlchemy's engine abstraction, allowing for a seamless transition to PostgreSQL or MySQL by simply updating the `DATABASE_URL` environment variable.
