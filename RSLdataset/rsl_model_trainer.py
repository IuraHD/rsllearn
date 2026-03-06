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
import json
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support
from utils import LANDMARKS_FOLDER, SAVED_MODELS_FOLDER, FRAMES_PER_SAMPLE

# Training settings
MAX_EPOCHS = 200
BATCH_SIZE = 32
VAL_SPLIT = 0.15
TEST_SPLIT = 0.15
PATIENCE = 20
NOISE = 0.01

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
        "total_samples": len(X),
        "train_samples": len(X_tr),
        "val_samples": len(X_val),
        "test_samples": len(X_te),
        "split_ratio": {"train": 0.7, "val": 0.15, "test": 0.15},
        "random_seed": 42
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
    dist = {cls: int(np.sum(np.argmax(y, axis=1) == i)) for i, cls in enumerate(classes)}
    pd.DataFrame(list(dist.items()), columns=['Class', 'Count']).to_csv(os.path.join(EVAL_FOLDER, "class_distribution.csv"), index=False)

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
        f.write(f"- **Total Samples:** {len(X)}\n")
        f.write(f"- **Classes:** {len(classes)} ({', '.join(classes)})\n")
        f.write(f"- **Input Shape:** {seq_len} frames x {feat} features\n\n")
        f.write("## Split Summary\n")
        f.write(f"- **Train:** {len(X_tr)}\n")
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
