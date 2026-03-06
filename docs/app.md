# RSLlingo Application Overview

## 🌌 System Vision
RSLlingo is a prototype e-learning platform specifically tailored for Romanian Sign Language (RSL). It bridges the gap between static video lessons and interactive AI-driven education by providing real-time feedback on sign production.

## 🏗️ Technical Architecture
The application follows a modern decoupled architecture:
1. **Frontend (React)**: Handles the UI, lesson flow, and client-side landmark extraction using MediaPipe.
2. **Backend (FastAPI)**: Manages progress tracking, gamification math, and hosts the TensorFlow/Keras inference engine.
3. **AI Pipeline**: A high-dimensional data relay where 90 frames of landmarks are captured on the client and classified on the server.

## 👥 User Roles
- **Student**: The primary learner. Can access all lessons, track progress, earn XP, and view leaderboards.
- **Admin**: Content creator role. Accesses the `/admin` interface to manage Units, Lessons, Tasks, and Achievements. Authenticated via `ADMIN_EMAIL` verification.

## 🎮 Gamification Engine
To ensure long-term engagement, the app implements several psychological "hooks":
- **XP & Levels**: Every lesson completed grants XP. Levels are calculated dynamically (XP / 1000).
- **Streaks**: Encourages daily practice. Streaks reset if a gap larger than 24 hours occurs between practice sessions.
- **Hearts System**: Users start each lesson with 5 hearts. Mistakes during sign tasks or multiple-choice components deplete hearts.
- **Achievements/Badges**: Visual milestones (e.g., "Perfect Lesson", "First Unit Completed") stored in the user profile.

## 📝 Task Types
The curriculum is built on four core task types:
1. **REPEAT_SIGN**: The user watches a video of a sign and repeats it in front of the camera. The AI validates the movement.
2. **TEXT_TO_SIGN**: The user is prompted with a word (e.g., "Bună") and must produce the corresponding sign without a visual reference.
3. **SIGN_TO_TEXT**: A multiple-choice task where the user identifies the meaning of a sign shown in a video.
4. **VIDEO_MULTIPLE_CHOICE**: The user is given a word and must choose the correct sign from three different video options.

## 🤖 AI Mascot
The mascot acts as a persistent companion. It "patrols" the bottom of the screen during lessons and on the learning path, providing a friendly, premium feel to the educational experience.
