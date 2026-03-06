from fastapi import APIRouter, Body
import numpy as np
import os

from ...core.config import BACKEND_DIR, PROJECT_DIR

router = APIRouter()

# Path to model assets.
# Paths can be overridden via `.env` (project root `.env` is loaded in core/config.py):
# - MODEL_PATH
# - CLASSES_PATH
#
# Defaults are chosen to match the training pipeline in `RSLdataset/`:
# - model:   RSLdataset/saved_models/best_model.h5
# - classes: RSLdataset/saved_models/sign_classes.txt
#
# If those don't exist, we fall back to legacy backend-local filenames.
def _resolve_asset_path(env_var: str, legacy_backend_default: str, preferred: str) -> str:
    env_val = os.getenv(env_var)
    if env_val:
        # Accept absolute paths, or resolve relative paths from backend/ for convenience.
        return os.path.abspath(os.path.join(str(BACKEND_DIR), env_val))

    # Prefer the trainer outputs if they exist.
    preferred_abs = os.path.abspath(os.path.join(str(PROJECT_DIR), preferred))
    if os.path.exists(preferred_abs):
        return preferred_abs

    return os.path.abspath(os.path.join(str(BACKEND_DIR), legacy_backend_default))


MODEL_PATH = _resolve_asset_path("MODEL_PATH", "model_latest.h5", os.path.join("RSLdataset", "saved_models", "best_model.h5"))
CLASSES_PATH = _resolve_asset_path("CLASSES_PATH", "classes.txt", os.path.join("RSLdataset", "saved_models", "sign_classes.txt"))

# Global model cache
_model = None
_classes = None

# Key face points used by trainer when feature size is 429.
# Keep in sync with RSLdataset/utils.py FACE_KEY_INDICES.
FACE_KEY_INDICES = sorted(set([
    10, 21, 54, 103, 127, 132, 150, 152, 172, 176, 284, 297, 361, 379, 389, 397, 400,
    33, 133, 144, 153, 158, 160, 263, 362, 373, 380, 385, 387,
    46, 52, 53, 55, 65, 276, 282, 283, 285, 295,
    1, 2, 4, 5, 6, 98, 168, 195, 327,
    13, 17, 61, 78, 82, 84, 87, 91, 146, 178, 181, 291, 308, 310, 311, 312, 314, 321, 375, 405,
]))

DEFAULT_SEQUENCE_LENGTH = 90
# Pose(33×3) + Face(key_indices×3) + LH(21×3) + RH(21×3)
DEFAULT_FEATURE_SIZE = 99 + (len(FACE_KEY_INDICES) * 3) + 63 + 63


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _read_trainer_meta() -> tuple[int | None, int | None]:
    """
    Read trainer metadata from `model_meta.txt` if present (RSLdataset trainer output).

    The trainer writes:
      features=429
      sequence_length=90
    """
    meta_path = os.path.join(os.path.dirname(MODEL_PATH), "model_meta.txt")
    if not os.path.exists(meta_path):
        return None, None

    features = None
    seq_len = None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if line.startswith("features="):
                    try:
                        features = int(line.split("=", 1)[1])
                    except ValueError:
                        pass
                elif line.startswith("sequence_length="):
                    try:
                        seq_len = int(line.split("=", 1)[1])
                    except ValueError:
                        pass
    except Exception:
        return None, None

    return seq_len, features


def get_sequence_length() -> int:
    # Env override first (used by backend prototype config).
    seq = _int_env("SEQUENCE_LENGTH", DEFAULT_SEQUENCE_LENGTH)
    if os.getenv("SEQUENCE_LENGTH"):
        return seq

    # Otherwise, try to use the trainer metadata if available.
    meta_seq, _ = _read_trainer_meta()
    return meta_seq if isinstance(meta_seq, int) else DEFAULT_SEQUENCE_LENGTH


def get_feature_size() -> int:
    # Support either FEATURE_SIZE (legacy) or TOTAL_FEATURES (matches dataset naming).
    if os.getenv("FEATURE_SIZE"):
        return _int_env("FEATURE_SIZE", DEFAULT_FEATURE_SIZE)
    if os.getenv("TOTAL_FEATURES"):
        return _int_env("TOTAL_FEATURES", DEFAULT_FEATURE_SIZE)

    # Otherwise, try to use the trainer metadata if available.
    _, meta_feat = _read_trainer_meta()
    return meta_feat if isinstance(meta_feat, int) else DEFAULT_FEATURE_SIZE


def load_classes():
    """Load class names from classes.txt."""
    path = CLASSES_PATH
    if not os.path.exists(path):
        # Trainer output default is `sign_classes.txt`. Allow pointing MODEL_PATH to the
        # training folder without requiring a rename/copy.
        alt = os.path.join(os.path.dirname(MODEL_PATH), "sign_classes.txt")
        if os.path.exists(alt):
            path = alt
        else:
            return []

    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def load_model():
    """Load and cache the trained model."""
    global _model, _classes

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model not deployed")

    try:
        from tensorflow.keras.models import load_model as keras_load_model
    except ImportError:
        raise RuntimeError("TensorFlow not installed on server")

    if _model is None:
        _model = keras_load_model(MODEL_PATH)
        _classes = load_classes()

    return _model, _classes


def _infer_expected_shape(model) -> tuple[int, int]:
    """Infer (sequence_length, feature_size) from model input shape, with env defaults fallback."""
    seq_len = get_sequence_length()
    feat_size = get_feature_size()

    try:
        input_shape = getattr(model, "input_shape", None)
        if isinstance(input_shape, list) and input_shape:
            input_shape = input_shape[0]
        if input_shape and len(input_shape) >= 3:
            if isinstance(input_shape[1], int):
                seq_len = input_shape[1]
            if isinstance(input_shape[2], int):
                feat_size = input_shape[2]
    except Exception:
        pass

    return seq_len, feat_size



@router.get("/sign/status")
def get_status():
    """Check if model is loaded and return expected model input contract."""
    model_exists = os.path.exists(MODEL_PATH)
    classes = load_classes()
    sequence_length = get_sequence_length()
    feature_size = get_feature_size()
    model_loaded = False
    model_error = None

    if model_exists:
        try:
            model, _ = load_model()
            sequence_length, feature_size = _infer_expected_shape(model)
            model_loaded = True
        except Exception as e:
            model_error = str(e)

    return {
        "success": True,
        "model_loaded": model_loaded,
        "model_exists": model_exists,
        "model_path": MODEL_PATH,
        "classes": classes,
        "classes_count": len(classes),
        "required_sequence_length": sequence_length,
        "required_feature_size": feature_size,
        "model_error": model_error,
    }


@router.get("/sign/classes")
def list_sign_classes():
    """List registered sign classes."""
    classes = load_classes()
    return {"success": True, "classes": classes}


@router.post("/sign/recognise")
def recognise_sign(data: dict = Body(...)):
    """
    Recognise a sign from landmark data.

    Expected data format:
    {
        "landmarks": [[...], [...], ...]  # Sequence of N frames
    }
    """
    try:
        landmarks = data.get("landmarks")
        if not landmarks:
            return {"success": False, "error": "No landmarks provided"}

        sequence = np.array(landmarks, dtype=np.float32)
        if len(sequence.shape) != 2:
            return {
                "success": False,
                "error": f"Invalid landmarks shape. Expected 2D array, got {sequence.shape}",
            }

        # If no model is deployed yet, return a stable stub response so
        # frontend lesson flow can be developed/tested.
        try:
            model, classes = load_model()
        except FileNotFoundError:
            expected_sequence_length = get_sequence_length()
            expected_feature_size = get_feature_size()
            return {
                "success": True,
                "prediction": "unknown",
                "confidence": 0.0,
                "all_predictions": [],
                "required_sequence_length": expected_sequence_length,
                "required_feature_size": expected_feature_size,
                "model_stub": True,
                "message": "Model not deployed (stub response)",
            }
        expected_sequence_length, expected_feature_size = _infer_expected_shape(model)

        raw_feature_size = int(sequence.shape[1]) if len(sequence.shape) == 2 else None

        if raw_feature_size != expected_feature_size:
            return {
                "success": False,
                "error": (
                    f"Invalid feature size. Expected {expected_feature_size}, got {raw_feature_size}. "
                ),
            }

        if sequence.shape[0] != expected_sequence_length:
            return {
                "success": False,
                "error": (
                    f"Invalid sequence length. Expected {expected_sequence_length}, got {sequence.shape[0]}"
                ),
            }

        if not classes:
            return {"success": False, "error": "No classes defined. Check classes.txt"}

        prediction = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]

        top_indices = np.argsort(prediction)[::-1][:5]
        results = []
        for idx in top_indices:
            sign_name = classes[idx] if idx < len(classes) else f"class_{int(idx)}"
            results.append({
                "sign": sign_name,
                "confidence": float(prediction[idx]),
            })

        best_idx = int(np.argmax(prediction))
        best_sign = classes[best_idx] if best_idx < len(classes) else f"class_{best_idx}"
        best_confidence = float(prediction[best_idx])

        return {
            "success": True,
            "prediction": best_sign,
            "confidence": best_confidence,
            "all_predictions": results,
            "required_sequence_length": expected_sequence_length,
            "required_feature_size": expected_feature_size,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
