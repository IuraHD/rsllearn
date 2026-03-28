"""
RSL Model Trainer — Train LSTM on collected keypoint data.

Usage:
    python rsl_model_trainer.py
    python rsl_model_trainer.py --epochs 300 --augment
    python rsl_model_trainer.py --device gpu --gpu-index 0
"""

import numpy as np
import os
import argparse
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import json
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support
from utils import (
    LANDMARKS_FOLDER,
    SAVED_MODELS_FOLDER,
    FRAMES_PER_SAMPLE,
    NUM_FACE_KEY,
    configure_tensorflow_runtime,
    list_tensorflow_devices,
    find_idle_label,
    fit_feature_scaler,
    apply_feature_scaler,
    save_feature_scaler,
)

# Training settings
MAX_EPOCHS = 200
BATCH_SIZE = 32
VAL_SPLIT = 0.15
TEST_SPLIT = 0.15
PATIENCE = 20
POSE_FEATURES = 99
FACE_FEATURES = NUM_FACE_KEY * 3
HAND_FEATURES = 63
AUGMENT_COPIES_PER_SAMPLE = 3
SPATIAL_JITTER_STD = 0.003
MAX_ROTATION_DEGREES = 7.0
MIN_SPATIAL_SCALE = 0.97
MAX_SPATIAL_SCALE = 1.03
MAX_TRANSLATION = 0.02
MAX_TEMPORAL_SHIFT = 3
MAX_FRAME_DROPOUT_RATIO = 0.1
MAX_DUPLICATED_FRAMES = 4

EVAL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_outputs")


def _read_feature_size():
    """Read feature count from metadata or first .npy file."""
    meta = os.path.join(LANDMARKS_FOLDER, "_metadata.txt")
    if os.path.exists(meta):
        with open(meta) as f:
            for line in f:
                if line.startswith("features="): return int(line.strip().split("=")[1])
    for d in os.listdir(LANDMARKS_FOLDER):
        dp = os.path.join(LANDMARKS_FOLDER, d)
        if os.path.isdir(dp):
            for f in os.listdir(dp):
                if f.endswith(".npy"):
                    return np.load(os.path.join(dp, f)).shape[-1]
    return None


def _read_seq_length():
    """Read sequence length from metadata or first .npy file."""
    meta = os.path.join(LANDMARKS_FOLDER, "_metadata.txt")
    if os.path.exists(meta):
        with open(meta) as f:
            for line in f:
                if line.startswith("frames="): return int(line.strip().split("=")[1])
    return FRAMES_PER_SAMPLE


def load_data(classes, seq_len, max_samples_per_class=None):
    """Load .npy sequences for each class."""
    from tensorflow.keras.utils import to_categorical

    X, y = [], []
    label_map = {c: i for i, c in enumerate(classes)}
    for cls in classes:
        path = os.path.join(LANDMARKS_FOLDER, cls)
        if not os.path.isdir(path): continue
        n = 0
        files = sorted(f for f in os.listdir(path) if f.endswith(".npy"))
        if max_samples_per_class is not None:
            files = files[:max_samples_per_class]
        for f in files:
            try:
                s = np.load(os.path.join(path, f))
                if s.shape[0] != seq_len: continue
                X.append(s); y.append(label_map[cls]); n += 1
            except Exception: pass
        print(f"  {cls}: {n} sequences")
    return (np.array(X), to_categorical(y).astype(int)) if X else (np.array([]), np.array([]))


def _resample_sequence(sequence, target_len):
    """Linearly resample a sequence back to the fixed training length."""
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


def _split_feature_groups(sequence):
    """Split a flattened [T, F] landmark sequence into pose/face/hand tensors."""
    seq = np.asarray(sequence, dtype=np.float32)
    face_start = POSE_FEATURES
    left_hand_start = face_start + FACE_FEATURES
    right_hand_start = left_hand_start + HAND_FEATURES
    return (
        seq[:, :POSE_FEATURES].reshape(len(seq), 33, 3),
        seq[:, face_start:left_hand_start].reshape(len(seq), NUM_FACE_KEY, 3),
        seq[:, left_hand_start:right_hand_start].reshape(len(seq), 21, 3),
        seq[:, right_hand_start:].reshape(len(seq), 21, 3),
    )


def _merge_feature_groups(pose, face, left_hand, right_hand):
    """Merge pose/face/hand tensors back into the flattened [T, F] format."""
    return np.concatenate([
        pose.reshape(len(pose), -1),
        face.reshape(len(face), -1),
        left_hand.reshape(len(left_hand), -1),
        right_hand.reshape(len(right_hand), -1),
    ], axis=1).astype(np.float32)


def _apply_group_affine(group, angle_radians, scale, tx, ty):
    """Apply a small image-space affine transform while keeping missing landmarks at zero."""
    transformed = np.asarray(group, dtype=np.float32).copy()
    valid = np.any(np.abs(transformed) > 1e-8, axis=-1).reshape(-1)
    if not np.any(valid):
        return transformed

    center = np.array([0.5, 0.5], dtype=np.float32)
    rotation = np.array([
        [np.cos(angle_radians), -np.sin(angle_radians)],
        [np.sin(angle_radians),  np.cos(angle_radians)],
    ], dtype=np.float32)

    xy = transformed[..., :2].reshape(-1, 2)
    xy[valid] = ((xy[valid] - center) @ rotation.T) * scale + center + np.array([tx, ty], dtype=np.float32)
    transformed[..., :2] = np.clip(xy.reshape(transformed.shape[0], transformed.shape[1], 2), 0.0, 1.0)

    z = transformed[..., 2].reshape(-1)
    z[valid] *= scale
    transformed[..., 2] = z.reshape(transformed.shape[0], transformed.shape[1])
    return transformed


def _augment_spatial(sequence, jitter_std=SPATIAL_JITTER_STD):
    """Apply small landmark-safe affine transforms plus mild noise."""
    pose, face, left_hand, right_hand = _split_feature_groups(sequence)
    angle = np.deg2rad(np.random.uniform(-MAX_ROTATION_DEGREES, MAX_ROTATION_DEGREES))
    scale = np.random.uniform(MIN_SPATIAL_SCALE, MAX_SPATIAL_SCALE)
    tx = np.random.uniform(-MAX_TRANSLATION, MAX_TRANSLATION)
    ty = np.random.uniform(-MAX_TRANSLATION, MAX_TRANSLATION)

    augmented = _merge_feature_groups(
        _apply_group_affine(pose, angle, scale, tx, ty),
        _apply_group_affine(face, angle, scale, tx, ty),
        _apply_group_affine(left_hand, angle, scale, tx, ty),
        _apply_group_affine(right_hand, angle, scale, tx, ty),
    )

    noise = np.random.normal(0.0, jitter_std, augmented.shape).astype(np.float32)
    valid_mask = np.abs(augmented) > 1e-8
    augmented = augmented + (noise * valid_mask)
    return augmented.astype(np.float32)


def _augment_temporal(sequence):
    """Apply temporal shift plus mild frame dropout or duplication, then resample."""
    seq = np.asarray(sequence, dtype=np.float32).copy()
    shift = np.random.randint(-MAX_TEMPORAL_SHIFT, MAX_TEMPORAL_SHIFT + 1)
    if shift > 0:
        seq = np.concatenate([np.repeat(seq[:1], shift, axis=0), seq[:-shift]], axis=0)
    elif shift < 0:
        shift = abs(shift)
        seq = np.concatenate([seq[shift:], np.repeat(seq[-1:], shift, axis=0)], axis=0)

    if np.random.rand() < 0.5:
        max_drop = max(1, int(len(seq) * MAX_FRAME_DROPOUT_RATIO))
        drop_count = np.random.randint(1, max_drop + 1)
        keep_mask = np.ones(len(seq), dtype=bool)
        keep_mask[np.random.choice(len(seq), size=drop_count, replace=False)] = False
        seq = seq[keep_mask]
    else:
        duplicate_count = np.random.randint(1, MAX_DUPLICATED_FRAMES + 1)
        duplicate_indices = np.sort(np.random.choice(len(seq), size=duplicate_count, replace=True))
        expanded = []
        dup_ptr = 0
        for index, frame in enumerate(seq):
            expanded.append(frame)
            while dup_ptr < len(duplicate_indices) and duplicate_indices[dup_ptr] == index:
                expanded.append(frame)
                dup_ptr += 1
        seq = np.asarray(expanded, dtype=np.float32)

    return _resample_sequence(seq, len(sequence))


def augment(X, y):
    """Training-only augmentation with spatial, temporal, and combined copies."""
    augmented_X = list(np.asarray(X, dtype=np.float32))
    augmented_y = list(y)

    for i in range(len(X)):
        base = np.asarray(X[i], dtype=np.float32)

        spatial = _augment_spatial(base)
        temporal = _augment_temporal(base)
        combined = _augment_spatial(_augment_temporal(base), jitter_std=SPATIAL_JITTER_STD * 0.75)

        augmented_X.extend([spatial, temporal, combined])
        augmented_y.extend([y[i], y[i], y[i]])

    return np.array(augmented_X, dtype=np.float32), np.array(augmented_y)


def _print_dataset_warnings(classes, seq_len, counts):
    """Surface dataset issues that are likely to hurt live recognition."""
    idle_label = find_idle_label(classes)
    if not idle_label:
        print("Warning: no idle/no-sign class found. Live testing will be forced to map background frames to a sign.")
    else:
        print(f"Idle/background class detected: {idle_label}")

    if seq_len > 60:
        print(f"Warning: sequence length {seq_len} is long for isolated signs; 30-60 frames is usually more stable.")

    min_count = min(counts.values()) if counts else 0
    if min_count and min_count < 40:
        print(f"Warning: smallest class has only {min_count} samples. Aim for at least 60 per class for cleaner live behavior.")


def train(epochs=MAX_EPOCHS, do_augment=False, patience=PATIENCE,
          device="auto", gpu_index=None, max_samples_per_class=None):
    device_info = configure_tensorflow_runtime(device=device, gpu_index=gpu_index)
    print(f"Training execution device: {device_info['device_used']}")
    if not device_info["tensorflow_version"]:
        print("TensorFlow is not available. Training cannot continue.")
        return
    from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.layers import RNN, LSTMCell, Dense, Dropout
    from tensorflow.keras.models import Sequential

    if not os.path.exists(LANDMARKS_FOLDER):
        print("No landmarks folder. Run collector first."); return

    classes = sorted(d for d in os.listdir(LANDMARKS_FOLDER)
                     if os.path.isdir(os.path.join(LANDMARKS_FOLDER, d)))
    if not classes:
        print("No classes found."); return

    feat = _read_feature_size()
    seq_len = _read_seq_length()
    if not feat:
        print("Could not detect feature size."); return

    print(f"Classes: {classes} | Features: {feat} | Seq len: {seq_len}")
    print(f"Epochs: {epochs} | Augment: {do_augment} | Patience: {patience}")
    if max_samples_per_class is not None:
        print(f"Sample cap: {max_samples_per_class} per class")
    print(f"Split: {100-int((VAL_SPLIT+TEST_SPLIT)*100)}% train / {int(VAL_SPLIT*100)}% val / {int(TEST_SPLIT*100)}% test\n")

    X, y = load_data(classes, seq_len, max_samples_per_class)
    if len(X) == 0:
        print("No data loaded."); return
    raw_total_samples = len(X)
    print(f"\nTotal raw sequences: {raw_total_samples}")
    class_counts = {cls: int(np.sum(np.argmax(y, axis=1) == i)) for i, cls in enumerate(classes)}
    _print_dataset_warnings(classes, seq_len, class_counts)

    # Two-stage split: first hold out the test set, then split the remainder into train/val.
    # This ensures the test set is NEVER seen during training (not even for callbacks).
    X_rest, X_te, y_rest, y_te = train_test_split(
        X, y, test_size=TEST_SPLIT, random_state=42, stratify=y)
    val_ratio = VAL_SPLIT / (1 - TEST_SPLIT)  # fraction of the remainder
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_rest, y_rest, test_size=val_ratio, random_state=42, stratify=y_rest)
    raw_train_samples = len(X_tr)
    print(f"Raw split sizes -> Train: {raw_train_samples} | Val: {len(X_val)} | Test: {len(X_te)}")

    scaler = fit_feature_scaler(X_tr)

    if do_augment:
        X_tr, y_tr = augment(X_tr, y_tr)
        print(
            f"After training-only augmentation: {len(X_tr)} train sequences "
            f"({AUGMENT_COPIES_PER_SAMPLE} extra copies per raw training sample) | Val/Test unchanged"
        )

    X_tr = apply_feature_scaler(X_tr, scaler)
    X_val = apply_feature_scaler(X_val, scaler)
    X_te = apply_feature_scaler(X_te, scaler)
    print("Feature standardization: enabled (fit on raw training split only)")

    # Model
    model = Sequential([
        # Use the backend-native LSTM cell path so GPU backends like DirectML do not
        # require the CuDNN-only RNN kernel.
        RNN(LSTMCell(64), return_sequences=True, input_shape=(seq_len, feat)), Dropout(0.2),
        RNN(LSTMCell(128), return_sequences=True), Dropout(0.2),
        RNN(LSTMCell(64)), Dropout(0.2),
        Dense(64, activation="relu"), Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(len(classes), activation="softmax"),
    ])
    model.compile(optimizer="Adam", loss="categorical_crossentropy", metrics=["categorical_accuracy"])
    model.summary()

    os.makedirs(SAVED_MODELS_FOLDER, exist_ok=True)
    best = os.path.join(SAVED_MODELS_FOLDER, "best_model.h5")
    save_feature_scaler(scaler)

    history = model.fit(X_tr, y_tr, epochs=epochs, batch_size=BATCH_SIZE,
              validation_data=(X_val, y_val), verbose=1, callbacks=[
                  ModelCheckpoint(best, monitor="val_loss", save_best_only=True, verbose=1),
                  EarlyStopping(monitor="val_loss", patience=patience, restore_best_weights=True, verbose=1),
                  ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=10, min_lr=1e-6, verbose=1),
              ])

    # Evaluate on HELD-OUT test set (never used during training or callback tuning)
    print("\n" + "=" * 60)
    print("  FINAL EVALUATION (held-out test set)")
    print("=" * 60)
    yp = np.argmax(model.predict(X_te, verbose=0), axis=1)
    yt = np.argmax(y_te, axis=1)
    print(f"\nTest Accuracy: {np.mean(yp == yt):.2%}")
    print(classification_report(yt, yp, target_names=classes))

    cm = confusion_matrix(yt, yp)
    print("Confusion Matrix:")
    print("  " + "".join(f"{c[:8]:>10}" for c in classes))
    for i, c in enumerate(classes):
        print(f"{c[:10]:>10}" + "".join(f"{cm[i][j]:>10}" for j in range(len(classes))))

    # --- Dissertation-Ready Export ---
    os.makedirs(EVAL_FOLDER, exist_ok=True)
    print(f"\nExporting dissertation-ready outputs to {EVAL_FOLDER}...")

    # 1. metrics_summary.json
    acc = np.mean(yp == yt)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(yt, yp, average='macro')
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(yt, yp, average='weighted')
    
    metrics = {
        "test_accuracy": float(acc),
        "macro_precision": float(p_macro),
        "macro_recall": float(r_macro),
        "macro_f1_score": float(f1_macro),
        "weighted_precision": float(p_weighted),
        "weighted_recall": float(r_weighted),
        "weighted_f1_score": float(f1_weighted),
        "num_classes": len(classes),
        "sequence_length": seq_len,
        "feature_size": feat,
        "total_samples": raw_total_samples,
        "train_samples": raw_train_samples,
        "train_samples_after_augmentation": len(X_tr),
        "val_samples": len(X_val),
        "test_samples": len(X_te),
        "class_counts": class_counts,
        "max_samples_per_class": max_samples_per_class,
        "augmentation_enabled": bool(do_augment),
        "augmentation_copies_per_sample": AUGMENT_COPIES_PER_SAMPLE if do_augment else 0,
        "split_ratio": {"train": 0.7, "val": 0.15, "test": 0.15},
        "random_seed": 42,
        "idle_class_present": bool(find_idle_label(classes)),
        "feature_standardization": True,
        "device_used": device_info["device_used"],
        "device_request": device_info["requested_device"],
        "gpu_index_requested": device_info["requested_gpu_index"],
        "gpu_index_used": device_info["selected_gpu_index"],
        "tensorflow_version": device_info["tensorflow_version"],
        "visible_gpus": device_info["visible_gpus"],
        "memory_growth_enabled": device_info["memory_growth_enabled"],
    }
    with open(os.path.join(EVAL_FOLDER, "metrics_summary.json"), "w") as f:
        json.dump(metrics, f, indent=4)

    # 2. classification_report.csv
    report_dict = classification_report(yt, yp, target_names=classes, output_dict=True)
    pd.DataFrame(report_dict).transpose().to_csv(os.path.join(EVAL_FOLDER, "classification_report.csv"))

    # 3. confusion_matrix.csv
    cm_df = pd.DataFrame(cm, index=classes, columns=classes)
    cm_df.to_csv(os.path.join(EVAL_FOLDER, "confusion_matrix.csv"))

    # 4. confusion_matrix.png
    plt.figure(figsize=(10, 8))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Confusion Matrix')
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     ha="center", va="center",
                     color="white" if cm[i, j] > thresh else "black")
    
    plt.tight_layout()
    plt.savefig(os.path.join(EVAL_FOLDER, "confusion_matrix.png"))
    plt.close()

    # 5. training_history.png
    if history:
        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.plot(history.history['loss'], label='Train Loss')
        plt.plot(history.history['val_loss'], label='Val Loss')
        plt.title('Model Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        plt.subplot(1, 2, 2)
        plt.plot(history.history['categorical_accuracy'], label='Train Acc')
        plt.plot(history.history['val_categorical_accuracy'], label='Val Acc')
        plt.title('Model Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(EVAL_FOLDER, "training_history.png"))
        plt.close()

    # 6. class_distribution.csv
    pd.DataFrame(list(class_counts.items()), columns=['Class', 'Count']).to_csv(
        os.path.join(EVAL_FOLDER, "class_distribution.csv"), index=False)

    # 7. evaluation_predictions.csv
    preds_df = pd.DataFrame({
        'true_label': [classes[i] for i in yt],
        'predicted_label': [classes[i] for i in yp],
        'correct': yp == yt
    })
    preds_df.to_csv(os.path.join(EVAL_FOLDER, "evaluation_predictions.csv"), index=False)

    # 8. evaluation_report.md
    with open(os.path.join(EVAL_FOLDER, "evaluation_report.md"), "w") as f:
        f.write("# RSL Recognition Evaluation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Dataset Summary\n")
        f.write(f"- **Total Raw Samples:** {raw_total_samples}\n")
        f.write(f"- **Classes:** {len(classes)} ({', '.join(classes)})\n")
        f.write(f"- **Input Shape:** {seq_len} frames x {feat} features\n\n")
        f.write("## Split Summary\n")
        f.write(f"- **Train (raw):** {raw_train_samples}\n")
        f.write(f"- **Train (after augmentation):** {len(X_tr)}\n")
        f.write(f"- **Validation:** {len(X_val)}\n")
        f.write(f"- **Test (Held-out):** {len(X_te)}\n\n")
        f.write("## Final Metrics\n")
        f.write(f"- **Accuracy:** {acc:.2%}\n")
        f.write(f"- **Macro F1-Score:** {f1_macro:.4f}\n")
        f.write(f"- **Weighted F1-Score:** {f1_weighted:.4f}\n\n")
        f.write("## Class Analysis\n")
        f.write("| Class | Precision | Recall | F1-Score | Support |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for cls in classes:
            m = report_dict[cls]
            f.write(f"| {cls} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1-score']:.4f} | {m['support']} |\n")
        
        f.write("\n## Weakest Classes\n")
        sorted_f1 = sorted([(cls, report_dict[cls]['f1-score']) for cls in classes], key=lambda x: x[1])
        for cls, f1 in sorted_f1[:3]:
            f.write(f"- **{cls}**: F1-Score = {f1:.4f}\n")

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    model.save(os.path.join(SAVED_MODELS_FOLDER, f"rsl_{ts}.h5"))
    with open(os.path.join(SAVED_MODELS_FOLDER, "sign_classes.txt"), "w") as f:
        f.writelines(c + "\n" for c in classes)
    with open(os.path.join(SAVED_MODELS_FOLDER, "model_meta.txt"), "w") as f:
        f.write(f"features={feat}\nsequence_length={seq_len}\nfeature_standardization=true\n")

    print(f"\nSaved to {SAVED_MODELS_FOLDER}")
    return model


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="RSL Model Trainer")
    p.add_argument("--epochs", "-e", type=int, default=MAX_EPOCHS)
    p.add_argument("--augment", "-a", action="store_true")
    p.add_argument("--patience", "-p", type=int, default=PATIENCE)
    p.add_argument("--device", choices=["auto", "gpu", "cpu"], default="auto")
    p.add_argument("--gpu-index", type=int, default=None)
    p.add_argument("--max-samples-per-class", type=int, default=None)
    p.add_argument("--list-devices", action="store_true")
    a = p.parse_args()
    if a.list_devices:
        list_tensorflow_devices()
    else:
        train(a.epochs, a.augment, a.patience, a.device, a.gpu_index, a.max_samples_per_class)
