"""
Shared utilities for RSL dataset tools.
All common constants, MediaPipe setup, keypoint extraction, and drawing in one place.
"""

import cv2
import numpy as np
import os
import urllib.request

mp = None
mp_python = None
mp_vision = None

# =============================================================================
# PATHS
# =============================================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_FOLDER = os.path.join(PROJECT_DIR, "dataset")
LANDMARKS_FOLDER = os.path.join(DATASET_FOLDER, "landmarks")
CLIPS_FOLDER = os.path.join(DATASET_FOLDER, "clips")
SAVED_MODELS_FOLDER = os.path.join(PROJECT_DIR, "saved_models")
MP_MODELS_FOLDER = os.path.join(PROJECT_DIR, "mp_models")
FEATURE_SCALER_FILE = os.path.join(SAVED_MODELS_FOLDER, "feature_scaler.npz")

# =============================================================================
# RECORDING / TRAINING SETTINGS
# =============================================================================

SAMPLES_PER_SIGN = 60          # sequences per gesture
FRAMES_PER_SAMPLE = 60         # frames per sequence (~2 sec at 30fps)
DETECTION_THRESHOLD = 0.5
TRACKING_THRESHOLD = 0.5
MIN_SIGN_HAND_VISIBILITY_RATIO = 0.2
DEFAULT_MIN_CONFIDENCE = 0.8
PREDICTION_SMOOTHING_WINDOW = 5
STABLE_PREDICTION_COUNT = 3
IDLE_CLASS_LABELS = {
    "idle",
    "no sign",
    "no_sign",
    "background",
    "rest",
    "neutral",
}

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

DEFAULT_GPU_INDEX = 0


def normalize_label_name(name):
    """Normalize class labels for dataset and live-tester checks."""
    return (name or "").strip().lower().replace("-", " ").replace("_", " ")


def is_idle_label(name):
    """Return True when a class name represents a no-sign/background label."""
    return normalize_label_name(name) in IDLE_CLASS_LABELS


def find_idle_label(classes):
    """Find the first class label that should be treated as idle/no-sign."""
    for cls in classes or []:
        if is_idle_label(cls):
            return cls
    return None


def count_detected_hands(hand_res):
    """Return how many hands MediaPipe detected in the current frame."""
    if hand_res and hand_res.hand_landmarks:
        return len(hand_res.hand_landmarks)
    return 0


def fit_feature_scaler(X):
    """Fit a simple per-feature standardization model over [N, T, F] data."""
    flat = np.asarray(X, dtype=np.float32).reshape(-1, X.shape[-1])
    mean = flat.mean(axis=0)
    std = flat.std(axis=0)
    std[std < 1e-6] = 1.0
    return {"mean": mean.astype(np.float32), "std": std.astype(np.float32)}


def apply_feature_scaler(X, scaler):
    """Apply saved feature standardization to a sequence or batch."""
    if not scaler:
        return X
    mean = scaler["mean"]
    std = scaler["std"]
    return (np.asarray(X, dtype=np.float32) - mean) / std


def save_feature_scaler(scaler, path=FEATURE_SCALER_FILE):
    """Persist feature standardization values for live inference."""
    if not scaler:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez(path, mean=scaler["mean"], std=scaler["std"])


def load_feature_scaler(path=FEATURE_SCALER_FILE):
    """Load feature standardization values if a trained model saved them."""
    if not os.path.exists(path):
        return None
    data = np.load(path)
    return {"mean": data["mean"], "std": data["std"]}


def _normalize_device_request(device):
    device = (device or "auto").lower()
    if device not in {"auto", "gpu", "cpu"}:
        raise ValueError(f"Unsupported device request: {device}")
    return device


def _prepare_tensorflow_device_request(device="auto", gpu_index=None, list_devices=False):
    """Set per-process TensorFlow/DirectML visibility before TensorFlow import."""
    device = _normalize_device_request(device)

    if gpu_index is not None and gpu_index < 0:
        raise ValueError("gpu_index must be >= 0")

    if os.name != "nt":
        return {
            "requested_device": device,
            "requested_gpu_index": gpu_index,
            "selected_gpu_index": gpu_index,
            "dml_visible_devices": os.environ.get("DML_VISIBLE_DEVICES"),
        }

    if list_devices or device == "cpu":
        os.environ.pop("DML_VISIBLE_DEVICES", None)
        return {
            "requested_device": device,
            "requested_gpu_index": gpu_index,
            "selected_gpu_index": None,
            "dml_visible_devices": None,
        }

    selected_gpu_index = DEFAULT_GPU_INDEX if gpu_index is None else gpu_index
    os.environ["DML_VISIBLE_DEVICES"] = str(selected_gpu_index)
    return {
        "requested_device": device,
        "requested_gpu_index": gpu_index,
        "selected_gpu_index": selected_gpu_index,
        "dml_visible_devices": os.environ.get("DML_VISIBLE_DEVICES"),
    }


def list_tensorflow_devices():
    """Print TensorFlow-visible devices and exit cleanly."""
    request = _prepare_tensorflow_device_request(list_devices=True)

    try:
        import tensorflow as tf
    except Exception as exc:
        print(f"[TensorFlow] Warning: TensorFlow import failed: {exc}")
        return {
            "tensorflow_version": None,
            "available_cpus": [],
            "available_gpus": [],
            "requested_device": request["requested_device"],
        }

    cpus = tf.config.list_physical_devices("CPU")
    gpus = tf.config.list_physical_devices("GPU")

    info = {
        "tensorflow_version": tf.__version__,
        "available_cpus": [cpu.name for cpu in cpus],
        "available_gpus": [gpu.name for gpu in gpus],
        "requested_device": request["requested_device"],
        "default_gpu_index": DEFAULT_GPU_INDEX if gpus else None,
    }

    print(f"[TensorFlow] Version: {tf.__version__}")
    print(f"[TensorFlow] Available CPUs: {info['available_cpus']}")
    print(f"[TensorFlow] Available GPUs: {info['available_gpus']}")
    if gpus:
        print("[TensorFlow] Use --device gpu --gpu-index N to select a specific GPU.")
        if os.name == "nt":
            print(f"[TensorFlow] Default DirectML GPU index: {DEFAULT_GPU_INDEX}")
    else:
        print("[TensorFlow] No GPU devices are currently visible to TensorFlow.")

    return info


def configure_tensorflow_runtime(device="auto", gpu_index=None):
    """Configure TensorFlow for GPU-first execution with safe CPU fallback."""
    request = _prepare_tensorflow_device_request(device=device, gpu_index=gpu_index)
    info = {
        "tensorflow_version": None,
        "visible_gpus": [],
        "device_used": "CPU",
        "memory_growth_enabled": False,
        "dml_visible_devices": request["dml_visible_devices"],
        "requested_device": request["requested_device"],
        "requested_gpu_index": request["requested_gpu_index"],
        "selected_gpu_index": request["selected_gpu_index"],
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
    if info["dml_visible_devices"]:
        print(f"[TensorFlow] DirectML adapter filter: DML_VISIBLE_DEVICES={info['dml_visible_devices']}")

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

    if info["requested_device"] == "cpu":
        if gpus:
            try:
                tf.config.set_visible_devices([], "GPU")
                print("[TensorFlow] CPU execution requested. GPU devices disabled for this run.")
            except Exception as exc:
                info["warning"] = f"Could not disable GPUs for CPU-only execution: {exc}"
                print(f"[TensorFlow] Warning: {info['warning']}")
        else:
            print("[TensorFlow] CPU execution requested. No GPU was visible to TensorFlow.")
        print("[TensorFlow] Execution device: CPU")
        return info

    if not gpus:
        if info["requested_device"] == "gpu":
            print("[TensorFlow] Warning: Requested GPU execution, but no visible GPU matched the request.")
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
        if info["selected_gpu_index"] is not None:
            print(f"[TensorFlow] Selected GPU index: {info['selected_gpu_index']}")
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


def _load_mediapipe():
    """Import MediaPipe lazily so TensorFlow device selection happens first."""
    global mp, mp_python, mp_vision

    if mp is None or mp_python is None or mp_vision is None:
        import mediapipe as mp_module
        from mediapipe.tasks import python as mp_python_module
        from mediapipe.tasks.python import vision as mp_vision_module

        mp = mp_module
        mp_python = mp_python_module
        mp_vision = mp_vision_module

    return mp, mp_python, mp_vision

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


def create_landmarkers(mode=None):
    """Create pose, hand, face landmarkers. Defaults to VIDEO mode for temporal smoothing."""
    _, mp_python_local, mp_vision_local = _load_mediapipe()
    mode = mode or mp_vision_local.RunningMode.VIDEO
    ensure_models()

    def _opts(name):
        return mp_python_local.BaseOptions(model_asset_path=os.path.join(MP_MODELS_FOLDER, name))

    pose = mp_vision_local.PoseLandmarker.create_from_options(mp_vision_local.PoseLandmarkerOptions(
        base_options=_opts("pose_landmarker.task"), running_mode=mode,
        num_poses=1, min_pose_detection_confidence=DETECTION_THRESHOLD,
        min_tracking_confidence=TRACKING_THRESHOLD))

    hands = mp_vision_local.HandLandmarker.create_from_options(mp_vision_local.HandLandmarkerOptions(
        base_options=_opts("hand_landmarker.task"), running_mode=mode,
        num_hands=2, min_hand_detection_confidence=DETECTION_THRESHOLD,
        min_tracking_confidence=TRACKING_THRESHOLD))

    face = mp_vision_local.FaceLandmarker.create_from_options(mp_vision_local.FaceLandmarkerOptions(
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
    mp_local, _, _ = _load_mediapipe()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = mp_local.Image(image_format=mp_local.ImageFormat.SRGB, data=rgb)
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
