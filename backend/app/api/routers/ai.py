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


def _resolve_feature_scaler_path() -> str:
    env_val = os.getenv("FEATURE_SCALER_PATH")
    if env_val:
        return os.path.abspath(os.path.join(str(BACKEND_DIR), env_val))

    preferred = os.path.abspath(os.path.join(os.path.dirname(MODEL_PATH), "feature_scaler.npz"))
    if os.path.exists(preferred):
        return preferred

    return os.path.abspath(os.path.join(str(BACKEND_DIR), "feature_scaler.npz"))


FEATURE_SCALER_PATH = _resolve_feature_scaler_path()
TEMPORAL_VIEW_WINDOWS = (
    (0.0, 1.0),
    (0.05, 0.95),
    (0.1, 0.9),
    (0.15, 0.85),
    (0.2, 0.8),
)

# Global model cache
_model = None
_classes = None
_scaler = None

# Key face points used by trainer when feature size is 429.
# Keep in sync with RSLdataset/utils.py FACE_KEY_INDICES.
FACE_KEY_INDICES = sorted(set([
    10, 21, 54, 103, 127, 132, 150, 152, 172, 176, 284, 297, 361, 379, 389, 397, 400,
    33, 133, 144, 153, 158, 160, 263, 362, 373, 380, 385, 387,
    46, 52, 53, 55, 65, 276, 282, 283, 285, 295,
    1, 2, 4, 5, 6, 98, 168, 195, 327,
    13, 17, 61, 78, 82, 84, 87, 91, 146, 178, 181, 291, 308, 310, 311, 312, 314, 321, 375, 405,
]))

DEFAULT_SEQUENCE_LENGTH = 60
# Pose(33×3) + Face(key_indices×3) + LH(21×3) + RH(21×3)
DEFAULT_FEATURE_SIZE = 99 + (len(FACE_KEY_INDICES) * 3) + 63 + 63
IDLE_CLASS_LABELS = {
    "idle",
    "no sign",
    "no_sign",
    "background",
    "rest",
    "neutral",
}


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def normalize_label_name(name: str | None) -> str:
    return (name or "").strip().lower().replace("-", " ").replace("_", " ")


def _find_idle_index(classes: list[str]) -> int | None:
    for idx, cls in enumerate(classes):
        if normalize_label_name(cls) in IDLE_CLASS_LABELS:
            return idx
    return None


def _resample_sequence(sequence: np.ndarray, target_len: int) -> np.ndarray:
    seq = np.asarray(sequence, dtype=np.float32)
    if len(seq) == 0:
        return np.zeros((target_len, seq.shape[-1] if seq.ndim == 2 else 0), dtype=np.float32)
    if len(seq) == target_len:
        return seq
    if len(seq) == 1:
        return np.repeat(seq, target_len, axis=0)

    positions = np.linspace(0, len(seq) - 1, num=target_len, dtype=np.float32)
    lower = np.floor(positions).astype(int)
    upper = np.ceil(positions).astype(int)
    alpha = (positions - lower).reshape(-1, 1).astype(np.float32)
    return seq[lower] * (1.0 - alpha) + seq[upper] * alpha


def _crop_sequence(sequence: np.ndarray, start_ratio: float, end_ratio: float) -> np.ndarray:
    seq = np.asarray(sequence, dtype=np.float32)
    if len(seq) == 0:
        return seq

    start = max(0, min(len(seq) - 1, int(np.floor(len(seq) * start_ratio))))
    end = max(start + 1, min(len(seq), int(np.ceil(len(seq) * end_ratio))))
    return seq[start:end]


def _predict_temporal_views(
    model,
    sequence: np.ndarray,
    scaler,
    classes: list[str],
    expected_sequence_length: int,
    target_label: str | None = None,
):
    """Run a few temporal crops and choose the best-scoring view for the caller's use case."""
    normalized_target = normalize_label_name(target_label)
    target_idx = None
    if normalized_target:
        for idx, cls in enumerate(classes):
            if normalize_label_name(cls) == normalized_target:
                target_idx = idx
                break

    idle_idx = _find_idle_index(classes)
    view_predictions: list[dict] = []

    for start_ratio, end_ratio in TEMPORAL_VIEW_WINDOWS:
        cropped = _crop_sequence(sequence, start_ratio, end_ratio)
        if len(cropped) == 0:
            continue
        view_sequence = _resample_sequence(cropped, expected_sequence_length)
        if scaler:
            view_sequence = apply_feature_scaler(view_sequence, scaler)

        probs = model.predict(np.expand_dims(view_sequence, axis=0), verbose=0)[0]
        probs = np.asarray(probs, dtype=np.float32)
        top_idx = int(np.argmax(probs))
        top_conf = float(probs[top_idx])
        non_idle_conf = top_conf
        if idle_idx is not None and len(probs) > 1:
            masked = probs.copy()
            masked[idle_idx] = -1.0
            non_idle_conf = float(np.max(masked))

        target_conf = float(probs[target_idx]) if target_idx is not None else None
        view_predictions.append({
            "window": {"start_ratio": start_ratio, "end_ratio": end_ratio},
            "probs": probs,
            "top_idx": top_idx,
            "top_conf": top_conf,
            "non_idle_conf": non_idle_conf,
            "target_conf": target_conf,
            "is_idle_top1": idle_idx is not None and top_idx == idle_idx,
        })

    if not view_predictions:
        raise ValueError("No valid temporal views available for inference")

    selected = view_predictions[0]

    if target_idx is not None:
        selected = max(
            view_predictions,
            key=lambda item: (
                item["target_conf"] if item["target_conf"] is not None else -1.0,
                0 if item["is_idle_top1"] else 1,
                item["top_conf"],
            ),
        )
    elif idle_idx is not None and selected["is_idle_top1"]:
        selected = max(
            view_predictions,
            key=lambda item: (
                0 if item["is_idle_top1"] else 1,
                item["non_idle_conf"],
                item["top_conf"],
            ),
        )

    return selected, target_idx, idle_idx


def _read_trainer_meta() -> tuple[int | None, int | None]:
    """
    Read trainer metadata from `model_meta.txt` if present (RSLdataset trainer output).

    The trainer writes:
      features=429
      sequence_length=60
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
        from tensorflow.keras.layers import LSTMCell, RNN
        from tensorflow.keras.models import load_model as keras_load_model
    except ImportError:
        raise RuntimeError("TensorFlow not installed on server")

    class CompatibilityRNN(RNN):
        """Ignore legacy H5 config fields that newer Keras versions no longer accept."""

        def __init__(self, *args, **kwargs):
            kwargs.pop("time_major", None)
            super().__init__(*args, **kwargs)

        @classmethod
        def from_config(cls, config):
            config = dict(config)
            config.pop("time_major", None)
            return super().from_config(config)

    if _model is None:
        custom_objects = {
            "LSTMCell": LSTMCell,
            "RNN": CompatibilityRNN,
        }
        _model = keras_load_model(MODEL_PATH, compile=False, custom_objects=custom_objects)
        _classes = load_classes()

    return _model, _classes


def load_feature_scaler():
    """Load and cache trainer feature standardization values if available."""
    global _scaler

    if _scaler is not None:
        return _scaler

    if not os.path.exists(FEATURE_SCALER_PATH):
        return None

    data = np.load(FEATURE_SCALER_PATH)
    mean = np.asarray(data["mean"], dtype=np.float32)
    std = np.asarray(data["std"], dtype=np.float32)
    std[std < 1e-6] = 1.0
    _scaler = {"mean": mean, "std": std}
    return _scaler


def apply_feature_scaler(sequence: np.ndarray, scaler):
    """Apply the same per-feature standardization used during training."""
    if not scaler:
        return np.asarray(sequence, dtype=np.float32)
    return (np.asarray(sequence, dtype=np.float32) - scaler["mean"]) / scaler["std"]


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
    scaler_exists = os.path.exists(FEATURE_SCALER_PATH)
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
        "feature_scaler_path": FEATURE_SCALER_PATH,
        "classes": classes,
        "classes_count": len(classes),
        "required_sequence_length": sequence_length,
        "required_feature_size": feature_size,
        "feature_scaler_available": scaler_exists,
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

        scaler = load_feature_scaler()
        if scaler:
            if scaler["mean"].shape[0] != expected_feature_size:
                return {
                    "success": False,
                    "error": (
                        "Feature scaler size does not match the deployed model. "
                        f"Expected {expected_feature_size}, got {scaler['mean'].shape[0]}"
                    ),
                }
            sequence = np.asarray(sequence, dtype=np.float32)

        target_label = data.get("target_label") or data.get("targetLabel")
        try:
            top_k = int(data.get("top_k") or data.get("topK") or 5)
        except (TypeError, ValueError):
            top_k = 5
        top_k = max(1, min(top_k, len(classes)))

        selected_view, target_idx, idle_idx = _predict_temporal_views(
            model=model,
            sequence=sequence,
            scaler=scaler,
            classes=classes,
            expected_sequence_length=expected_sequence_length,
            target_label=target_label,
        )
        prediction = selected_view["probs"]

        top_indices = np.argsort(prediction)[::-1][:top_k]
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
        target_confidence = float(prediction[target_idx]) if target_idx is not None else None
        target_rank = None
        if target_idx is not None:
            order = np.argsort(prediction)[::-1]
            target_rank = int(np.where(order == target_idx)[0][0]) + 1
        idle_confidence = float(prediction[idle_idx]) if idle_idx is not None else None

        return {
            "success": True,
            "prediction": best_sign,
            "confidence": best_confidence,
            "all_predictions": results,
            "target_label": target_label,
            "target_confidence": target_confidence,
            "target_rank": target_rank,
            "idle_confidence": idle_confidence,
            "selected_window": selected_view["window"],
            "required_sequence_length": expected_sequence_length,
            "required_feature_size": expected_feature_size,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
