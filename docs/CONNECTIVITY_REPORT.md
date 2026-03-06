# Connectivity & Integration Report

## 🛰️ Frontend-Backend Bridge
The RSLlingo frontend communicates with the FastAPI backend via a centralized `api.ts` service layer. This ensures consistent error handling and header injection across the entire application.

## 🔗 Integration Points
### 1. Unified API Service
- **Base URL**: Defaults to `http://localhost:3001/api`.
- **Request Interceptor**: Automatically attaches the `X-User-Id` from `localStorage` to every outgoing request.
- **Response Handling**: Standardized parsing of `{ success: true, data: ... }` wrappers.

### 2. Environment Variables
The system relies on a few critical environment variables for connectivity:
- **Frontend**: `VITE_API_URL` (optional, defaults to local).
- **Backend**: 
  - `MODEL_PATH`: Location of the `.h5` inference model.
  - `CLASSES_PATH`: Path to the sign label registry.
  - `ADMIN_EMAIL`: The account granted administrative privileges.

### 3. AI Data Relay (Critical Path)
The most data-intensive part of the application is the landmark relay:
1. **Frontend**: Samples 30fps video -> MediaPipe extraction -> Buffers 90 frames.
2. **Transfer**: The resulting JSON payload (~1.5MB) is sent via `POST`.
3. **Backend**: deserializes, runs tensor operations, and returns a small JSON prediction string.

## ✅ Health Checks
- **Heartbeat**: The frontend verifies the backend status on the splash screen.
- **Model Verification**: The `GET /api/sign/status` endpoint confirms the AI model is ready before allowing the user to start a Cam-based lesson.

## ⚠️ Known Limitations
- **Prototype Auth**: The lack of JWT/OAuth2 means the `X-User-Id` is strictly for demonstration purposes and lacks cryptographic signing.
- **Media Serving**: To simplify the prototype, lesson videos are served as static assets from the frontend rather than a streaming backend or S3 bucket.
