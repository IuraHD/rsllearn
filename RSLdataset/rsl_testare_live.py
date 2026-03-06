"""
RSL Live Tester — Real-time sign recognition with confidence bars.

Usage:
    python rsl_testare_live.py
    python rsl_testare_live.py --model saved_models/best_model.h5
"""

import cv2
import numpy as np
import os
import argparse
import time
from utils import (
    SAVED_MODELS_FOLDER, FRAMES_PER_SAMPLE,
    create_landmarkers, close_landmarkers, detect_landmarks,
    extract_keypoints, draw_landmarks,
    configure_tensorflow_runtime,
)

MIN_CONFIDENCE = 0.5

BAR_COLORS = [
    (46,204,113),(52,152,219),(231,76,60),(241,196,15),(155,89,182),
    (230,126,34),(26,188,156),(52,73,94),(243,156,18),(192,57,43),
    (22,160,133),(41,128,185),(142,68,173),(39,174,96),(211,84,0),
]


def _load_classes():
    path = os.path.join(SAVED_MODELS_FOLDER, "sign_classes.txt")
    if not os.path.exists(path): return []
    with open(path) as f:
        return [l.strip() for l in f if l.strip()]


def _load_seq_len():
    meta = os.path.join(SAVED_MODELS_FOLDER, "model_meta.txt")
    if os.path.exists(meta):
        with open(meta) as f:
            for line in f:
                if line.startswith("sequence_length="): return int(line.strip().split("=")[1])
    return FRAMES_PER_SAMPLE


def draw_confidence(img, classes, probs, W, H):
    """Draw confidence bars + prediction overlay."""
    n = len(classes)
    if not n: return

    # Panel
    pw, bh, gap, pad = 280, 22, 6, 15
    ph = pad*2 + n*(bh+gap) + 50
    px, py = W-pw-15, H-ph-15

    ov = img.copy()
    cv2.rectangle(ov, (px,py), (px+pw,py+ph), (30,30,30), -1)
    cv2.addWeighted(ov, 0.75, img, 0.25, 0, img)
    cv2.rectangle(img, (px,py), (px+pw,py+ph), (80,80,80), 1)
    cv2.putText(img, "PREDICTIONS", (px+pad,py+25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)

    mbw = pw - 2*pad - 62
    bi = np.argmax(probs)

    for i, (name, p) in enumerate(zip(classes, probs)):
        y = py + 45 + i*(bh+gap)
        col = BAR_COLORS[i % len(BAR_COLORS)]
        bx = px + pad + 62
        cv2.putText(img, name[:8], (px+pad, y+bh-6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
        cv2.rectangle(img, (bx,y), (bx+mbw,y+bh), (60,60,60), -1)
        fw = int(mbw * p)
        if fw > 0: cv2.rectangle(img, (bx,y), (bx+fw,y+bh), col, -1)
        cv2.putText(img, f"{p*100:.0f}%", (bx+fw+4,y+bh-5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200,200,200), 1)

    # Big prediction
    if probs[bi] >= MIN_CONFIDENCE:
        txt = f"{classes[bi]} ({probs[bi]*100:.1f}%)"
        col = BAR_COLORS[bi % len(BAR_COLORS)]
        sz = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
        ov2 = img.copy()
        cv2.rectangle(ov2, (10,10), (10+sz[0]+20, 10+sz[1]+20), (20,20,20), -1)
        cv2.addWeighted(ov2, 0.7, img, 0.3, 0, img)
        cv2.putText(img, txt, (20, 10+sz[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, col, 3)
    else:
        cv2.putText(img, "...", (20,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (120,120,120), 2)


def run(model_path=None):
    device_info = configure_tensorflow_runtime()
    print(f"Live tester execution device: {device_info['device_used']}")
    if not device_info["tensorflow_version"]:
        print("TensorFlow is not available. Live inference cannot continue.")
        return
    from tensorflow.keras.models import load_model

    model_path = model_path or os.path.join(SAVED_MODELS_FOLDER, "best_model.h5")
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}"); return

    model = load_model(model_path)
    classes = _load_classes()
    if not classes: print("No classes file."); return
    seq_len = _load_seq_len()

    print(f"Model: {model_path}")
    print(f"Classes: {classes} | Buffer: {seq_len} frames")

    pose_lm, hand_lm, face_lm = create_landmarkers()
    ts = 0

    cam = cv2.VideoCapture(0)
    if not cam.isOpened(): print("No webcam."); return
    W = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print("Press 'q' to quit\n")
    buf = []

    while cam.isOpened():
        ok, frame = cam.read()
        if not ok: break

        ts += 33
        pose_r, hand_r, face_r = detect_landmarks(pose_lm, hand_lm, face_lm, frame, ts)

        d = frame.copy()
        draw_landmarks(d, pose_r, hand_r, face_r)

        buf.append(extract_keypoints(pose_r, hand_r, face_r))
        if len(buf) > seq_len: buf = buf[-seq_len:]

        if len(buf) == seq_len:
            start_time = time.time()
            pred = model.predict(np.expand_dims(np.array(buf), 0), verbose=0)[0]
            latency = (time.time() - start_time) * 1000  # ms
            
            draw_confidence(d, classes, pred, W, H)
            
            # Dissertation-ready console logging
            bi = np.argmax(pred)
            if pred[bi] >= MIN_CONFIDENCE:
                print(f"[LIVE EVAL] Prediction: {classes[bi]} | Confidence: {pred[bi]:.4f} | Latency: {latency:.2f}ms")
        else:
            cv2.putText(d, f"Buffering {len(buf)*100//seq_len}%", (20,50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,200,255), 2)

        cv2.imshow("RSL Live Tester", d)
        if cv2.waitKey(1) & 0xFF == ord("q"): break

    close_landmarkers(pose_lm, hand_lm, face_lm)
    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="RSL Live Tester")
    p.add_argument("--model", "-m", type=str, default=None)
    run(p.parse_args().model)
