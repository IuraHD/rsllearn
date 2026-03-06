# API Documentation 🚀

The RSLlingo API is a RESTful service built with FastAPI. It uses JSON for all request and response bodies.

## 🔑 Authentication
The current prototype uses a header-based authentication mechanism.
- **Header**: `X-User-Id`
- **Value**: The unique UUID of the user.

## 👤 User Endpoints
### `POST /api/user/login`
Authenticates a user and returns their profile.
- **Body**: `{ "email": "...", "password": "..." }`

### `POST /api/user/register`
Creates a new user account.
- **Body**: `{ "displayName": "...", "email": "...", "password": "..." }`

### `GET /api/user/profile`
Fetches the current user's statistics, level, and badges.

### `POST /api/user/complete-lesson`
Submitted when a lesson is finished to update progress and XP.
- **Body**: 
  ```json
  {
    "lessonId": "...",
    "unitId": "...",
    "xpEarned": 50,
    "tasksCompleted": 10,
    "totalTasks": 10,
    "mistakes": 1
  }
  ```

## 📚 Lesson & Content Endpoints
### `GET /api/lessons/learning-path`
Returns the full hierarchy of Units and Lessons available to the user.

### `GET /api/lessons/{lesson_id}`
Fetches the details and tasks for a specific lesson.

## 🤖 AI & Sign Recognition
### `POST /api/sign/recognise`
Performs inference on a sequence of landmarks.
- **Body**: `{ "landmarks": [[...], [...]] }` (90x429 array)
- **Returns**: `{ "prediction": "hello", "confidence": 0.98 }`

### `GET /api/sign/status`
Returns the status of the AI model (loaded model name, version, and input shape requirements).

## 🏆 Social & Gamification
### `GET /api/user/leaderboard`
Returns the top 10 users ranked by total XP.

### `GET /api/user/achievements`
Returns the complete list of available achievements in the system.

## 🛠️ Admin Endpoints (Gated)
Admin endpoints are located under `/api/admin/*` and require the authenticated user's email to match the `ADMIN_EMAIL` environment variable.
- `POST /api/admin/units`: Create a new unit.
- `PUT /api/admin/lessons/{id}`: Update lesson metadata.
- `POST /api/admin/tasks`: Add a task to a lesson.
- `DELETE /api/admin/tasks/{id}`: Remove a task.
