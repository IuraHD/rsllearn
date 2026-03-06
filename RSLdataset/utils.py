"""
Shared utilities for RSL dataset tools.
All common constants, MediaPipe setup, keypoint extraction, and drawing in one place.
"""

import cv2
import numpy as np
import os
import urllib.request
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# =============================================================================
# PATHS
# =============================================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_FOLDER = os.path.join(PROJECT_DIR, "dataset")
LANDMARKS_FOLDER = os.path.join(DATASET_FOLDER, "landmarks")
CLIPS_FOLDER = os.path.join(DATASET_FOLDER, "clips")
SAVED_MODELS_FOLDER = os.path.join(PROJECT_DIR, "saved_models")
MP_MODELS_FOLDER = os.path.join(PROJECT_DIR, "mp_models")

# =============================================================================
# RECORDING / TRAINING SETTINGS
# =============================================================================

SAMPLES_PER_SIGN = 30          # sequences per gesture
FRAMES_PER_SAMPLE = 90         # frames per sequence (~3 sec at 30fps)
DETECTION_THRESHOLD = 0.5
TRACKING_THRESHOLD = 0.5

# =============================================================================
# MEDIAPIPE MODEL URLS (lite for speed)
# =============================================================================

MODEL_URLS = {
    "pose_landmarker.task":
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
    "hand_landmarker.task":
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    "face_landmarker.task":
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
}

# =============================================================================
# KEY FACE LANDMARK INDICES
# ~68 key points: face outline, eyes, eyebrows, nose, lips
# =============================================================================

FACE_KEY_INDICES = sorted(set([
    # Face outline (17)
    10, 21, 54, 103, 127, 132, 150, 152, 172, 176, 284, 297, 361, 379, 389, 397, 400,
    # Eyes (12)
    33, 133, 144, 153, 158, 160, 263, 362, 373, 380, 385, 387,
    # Eyebrows (10)
    46, 52, 53, 55, 65, 276, 282, 283, 285, 295,
    # Nose (9)
    1, 2, 4, 5, 6, 98, 168, 195, 327,
    # Lips (20)
    13, 17, 61, 78, 82, 84, 87, 91, 146, 178, 181, 291, 308, 310, 311, 312, 314, 321, 375, 405,
]))

NUM_FACE_KEY = len(FACE_KEY_INDICES)
# Pose(33×3) + Face(~68×3) + LH(21×3) + RH(21×3)
TOTAL_FEATURES = 99 + NUM_FACE_KEY * 3 + 63 + 63


def configure_tensorflow_runtime():
    """Configure TensorFlow for GPU-first execution with safe CPU fallback."""
    info = {
        "tensorflow_version": None,
        "visible_gpus": [],
        "device_used": "CPU",
        "memory_growth_enabled": False,
    }

    try:
        import tensorflow as tf
    except Exception as exc:
        info["warning"] = f"TensorFlow import failed: {exc}"
        print(f"[TensorFlow] Warning: {info['warning']}")
        print("[TensorFlow] Execution device: CPU")
        return info

    info["tensorflow_version"] = tf.__version__
    print(f"[TensorFlow] Version: {tf.__version__}")

    try:
        gpus = tf.config.list_physical_devices("GPU")
        info["visible_gpus"] = [gpu.name for gpu in gpus]
        print(f"[TensorFlow] Visible GPUs: {info['visible_gpus']}")
    except Exception as exc:
        info["warning"] = f"Could not query visible GPUs: {exc}"
        print(f"[TensorFlow] Warning: {info['warning']}")
        print("[TensorFlow] Falling back to CPU execution.")
        print("[TensorFlow] Execution device: CPU")
        return info

    if not gpus:
        print("[TensorFlow] No GPU detected. Falling back to CPU execution.")
        print("[TensorFlow] Execution device: CPU")
        return info

    try:
        memory_growth_enabled = True
        for gpu in gpus:
            try:
                tf.config.experimental.set_memory_growth(gpu, True)
            except Exception as exc:
                memory_growth_enabled = False
                print(f"[TensorFlow] Warning: Could not enable memory growth for {gpu.name}: {exc}")

        info["memory_growth_enabled"] = memory_growth_enabled

        logical_gpus = tf.config.list_logical_devices("GPU")
        if not logical_gpus:
            raise RuntimeError("No logical GPU devices became available.")

        print("[TensorFlow] GPU detected. TensorFlow will use the default visible GPU.")
        if memory_growth_enabled:
            print("[TensorFlow] Memory growth enabled for visible GPU(s).")
        else:
            print("[TensorFlow] Memory growth could not be enabled; continuing with TensorFlow defaults.")
        print("[TensorFlow] Execution device: GPU")
        info["device_used"] = "GPU"
        return info
    except Exception as exc:
        info["warning"] = f"GPU initialization failed: {exc}"
        print(f"[TensorFlow] Warning: {info['warning']}")
        try:
            tf.config.set_visible_devices([], "GPU")
        except Exception as disable_exc:
            print(f"[TensorFlow] Warning: Could not disable GPUs after failure: {disable_exc}")
        print("[TensorFlow] Falling back to CPU execution.")
        print("[TensorFlow] Execution device: CPU")
        info["device_used"] = "CPU"
        info["memory_growth_enabled"] = False
        return info

# =============================================================================
# DRAWING CONNECTIONS
# =============================================================================

POSE_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,7),(0,4),(4,5),(5,6),(6,8),
    (9,10),(11,12),(11,13),(13,15),(12,14),(14,16),
    (11,23),(12,24),(23,24),(23,25),(24,26),(25,27),(26,28),
]
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),(0,17),
]


# =============================================================================
# MODEL MANAGEMENT
# =============================================================================

def ensure_models():
    """Download MediaPipe model files if missing."""
    os.makedirs(MP_MODELS_FOLDER, exist_ok=True)
    for name, url in MODEL_URLS.items():
        path = os.path.join(MP_MODELS_FOLDER, name)
        if not os.path.exists(path):
            print(f"  Downloading {name}...")
            urllib.request.urlretrieve(url, path)


def create_landmarkers(mode=mp_vision.RunningMode.VIDEO):
    """Create pose, hand, face landmarkers. Defaults to VIDEO mode for temporal smoothing."""
    ensure_models()
    def _opts(name):
        return mp_python.BaseOptions(model_asset_path=os.path.join(MP_MODELS_FOLDER, name))

    pose = mp_vision.PoseLandmarker.create_from_options(mp_vision.PoseLandmarkerOptions(
        base_options=_opts("pose_landmarker.task"), running_mode=mode,
        num_poses=1, min_pose_detection_confidence=DETECTION_THRESHOLD,
        min_tracking_confidence=TRACKING_THRESHOLD))

    hands = mp_vision.HandLandmarker.create_from_options(mp_vision.HandLandmarkerOptions(
        base_options=_opts("hand_landmarker.task"), running_mode=mode,
        num_hands=2, min_hand_detection_confidence=DETECTION_THRESHOLD,
        min_tracking_confidence=TRACKING_THRESHOLD))

    face = mp_vision.FaceLandmarker.create_from_options(mp_vision.FaceLandmarkerOptions(
        base_options=_opts("face_landmarker.task"), running_mode=mode,
        num_faces=1, min_face_detection_confidence=DETECTION_THRESHOLD,
        min_tracking_confidence=TRACKING_THRESHOLD))

    return pose, hands, face


def close_landmarkers(pose, hands, face):
    pose.close(); hands.close(); face.close()


# =============================================================================
# DETECTION
# =============================================================================

def detect_landmarks(pose_lm, hand_lm, face_lm, frame, timestamp_ms):
    """Run all 3 detectors on a BGR frame. Returns (pose_res, hand_res, face_res)."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    return (
        pose_lm.detect_for_video(img, timestamp_ms),
        hand_lm.detect_for_video(img, timestamp_ms),
        face_lm.detect_for_video(img, timestamp_ms),
    )


# =============================================================================
# KEYPOINT EXTRACTION
# =============================================================================

def extract_keypoints(pose_res, hand_res, face_res):
    """Extract and flatten keypoints into a single vector of shape (TOTAL_FEATURES,)."""
    # Pose: 33 × 3
    pose = (np.array([[lm.x, lm.y, lm.z] for lm in pose_res.pose_landmarks[0]]).flatten()
            if pose_res.pose_landmarks else np.zeros(99))

    # Face: key indices × 3
    if face_res.face_landmarks:
        fl = face_res.face_landmarks[0]
        face = np.array([[fl[i].x, fl[i].y, fl[i].z] for i in FACE_KEY_INDICES]).flatten()
    else:
        face = np.zeros(NUM_FACE_KEY * 3)

    # Hands: left and right
    lh, rh = np.zeros(63), np.zeros(63)
    if hand_res.hand_landmarks:
        for lms, hd in zip(hand_res.hand_landmarks, hand_res.handedness):
            data = np.array([[l.x, l.y, l.z] for l in lms]).flatten()
            if hd[0].category_name == "Left":
                lh = data
            else:
                rh = data

    return np.concatenate([pose, face, lh, rh])


# =============================================================================
# DRAWING
# =============================================================================

def draw_landmarks(image, pose_res, hand_res, face_res):
    """Draw all landmarks on the image (modifies in-place)."""
    h, w = image.shape[:2]

    # Pose
    if pose_res.pose_landmarks:
        pts = pose_res.pose_landmarks[0]
        for a, b in POSE_CONNECTIONS:
            cv2.line(image, (int(pts[a].x*w), int(pts[a].y*h)),
                     (int(pts[b].x*w), int(pts[b].y*h)), (80, 44, 121), 2)
        for lm in pts:
            cv2.circle(image, (int(lm.x*w), int(lm.y*h)), 3, (80, 22, 10), -1)

    # Hands
    if hand_res.hand_landmarks:
        for lms, hd in zip(hand_res.hand_landmarks, hand_res.handedness):
            is_left = hd[0].category_name == "Left"
            cl, cd = ((121,44,250), (121,22,76)) if is_left else ((245,66,230), (245,117,66))
            for a, b in HAND_CONNECTIONS:
                cv2.line(image, (int(lms[a].x*w), int(lms[a].y*h)),
                         (int(lms[b].x*w), int(lms[b].y*h)), cl, 2)
            for lm in lms:
                cv2.circle(image, (int(lm.x*w), int(lm.y*h)), 4, cd, -1)

    # Face key points
    if face_res.face_landmarks:
        fl = face_res.face_landmarks[0]
        for i in FACE_KEY_INDICES:
            cv2.circle(image, (int(fl[i].x*w), int(fl[i].y*h)), 1, (80, 255, 121), -1)
