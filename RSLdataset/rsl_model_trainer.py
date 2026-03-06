"""
RSL Model Trainer — Train LSTM on collected keypoint data.

Usage:
    python rsl_model_trainer.py
    python rsl_model_trainer.py --epochs 300 --augment
"""

import numpy as np
import os
import argparse
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from utils import LANDMARKS_FOLDER, SAVED_MODELS_FOLDER, FRAMES_PER_SAMPLE

# Training settings
MAX_EPOCHS = 200
BATCH_SIZE = 32
VAL_SPLIT = 0.15
TEST_SPLIT = 0.15
PATIENCE = 20
NOISE = 0.01


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


def load_data(classes, seq_len):
    """Load .npy sequences for each class."""
    X, y = [], []
    label_map = {c: i for i, c in enumerate(classes)}
    for cls in classes:
        path = os.path.join(LANDMARKS_FOLDER, cls)
        if not os.path.isdir(path): continue
        n = 0
        for f in os.listdir(path):
            if not f.endswith(".npy"): continue
            try:
                s = np.load(os.path.join(path, f))
                if s.shape[0] != seq_len: continue
                X.append(s); y.append(label_map[cls]); n += 1
            except Exception: pass
        print(f"  {cls}: {n} sequences")
    return (np.array(X), to_categorical(y).astype(int)) if X else (np.array([]), np.array([]))


def augment(X, y):
    """Gaussian noise + time-shift augmentation."""
    aX, ay = list(X), list(y)
    for i in range(len(X)):
        aX.append(X[i] + np.random.normal(0, NOISE, X[i].shape)); ay.append(y[i])
        shifted = np.roll(X[i], 1, axis=0); shifted[0] = X[i][0]
        aX.append(shifted); ay.append(y[i])
    return np.array(aX), np.array(ay)


def train(epochs=MAX_EPOCHS, do_augment=False, patience=PATIENCE):
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
    print(f"Split: {100-int((VAL_SPLIT+TEST_SPLIT)*100)}% train / {int(VAL_SPLIT*100)}% val / {int(TEST_SPLIT*100)}% test\n")

    X, y = load_data(classes, seq_len)
    if len(X) == 0:
        print("No data loaded."); return
    print(f"\nTotal: {len(X)} sequences")

    if do_augment:
        X, y = augment(X, y)
        print(f"After augmentation: {len(X)}")

    # Two-stage split: first hold out the test set, then split the remainder into train/val.
    # This ensures the test set is NEVER seen during training (not even for callbacks).
    X_rest, X_te, y_rest, y_te = train_test_split(
        X, y, test_size=TEST_SPLIT, random_state=42, stratify=y)
    val_ratio = VAL_SPLIT / (1 - TEST_SPLIT)  # fraction of the remainder
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_rest, y_rest, test_size=val_ratio, random_state=42, stratify=y_rest)
    print(f"Train: {len(X_tr)} | Val: {len(X_val)} | Test: {len(X_te)}")

    # Model
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(seq_len, feat)), Dropout(0.2),
        LSTM(128, return_sequences=True), Dropout(0.2),
        LSTM(64), Dropout(0.2),
        Dense(64, activation="relu"), Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(len(classes), activation="softmax"),
    ])
    model.compile(optimizer="Adam", loss="categorical_crossentropy", metrics=["categorical_accuracy"])
    model.summary()

    os.makedirs(SAVED_MODELS_FOLDER, exist_ok=True)
    best = os.path.join(SAVED_MODELS_FOLDER, "best_model.h5")

    model.fit(X_tr, y_tr, epochs=epochs, batch_size=BATCH_SIZE,
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

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    model.save(os.path.join(SAVED_MODELS_FOLDER, f"rsl_{ts}.h5"))
    with open(os.path.join(SAVED_MODELS_FOLDER, "sign_classes.txt"), "w") as f:
        f.writelines(c + "\n" for c in classes)
    with open(os.path.join(SAVED_MODELS_FOLDER, "model_meta.txt"), "w") as f:
        f.write(f"features={feat}\nsequence_length={seq_len}\n")

    print(f"\nSaved to {SAVED_MODELS_FOLDER}")
    return model


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="RSL Model Trainer")
    p.add_argument("--epochs", "-e", type=int, default=MAX_EPOCHS)
    p.add_argument("--augment", "-a", action="store_true")
    p.add_argument("--patience", "-p", type=int, default=PATIENCE)
    a = p.parse_args()
    train(a.epochs, a.augment, a.patience)
