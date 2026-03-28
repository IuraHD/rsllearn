"""
RSL Live Tester — Real-time sign recognition with confidence bars.

Usage:
    python rsl_testare_live.py
    python rsl_testare_live.py --model saved_models/best_model.h5
    python rsl_testare_live.py --device gpu --gpu-index 0
"""

import cv2
import numpy as np
import os
import argparse
import time
from collections import Counter, deque
from utils import (
    SAVED_MODELS_FOLDER, FRAMES_PER_SAMPLE,
    create_landmarkers, close_landmarkers, detect_landmarks,
    extract_keypoints, draw_landmarks,
    configure_tensorflow_runtime,
    list_tensorflow_devices,
    count_detected_hands,
    find_idle_label,
    load_feature_scaler,
    apply_feature_scaler,
    DEFAULT_MIN_CONFIDENCE,
    PREDICTION_SMOOTHING_WINDOW,
    STABLE_PREDICTION_COUNT,
    MIN_SIGN_HAND_VISIBILITY_RATIO,
)

MIN_CONFIDENCE = DEFAULT_MIN_CONFIDENCE
REALTIME_PRE_ROLL_FRAMES = 8
REALTIME_MIN_ACTIVE_FRAMES = 18
REALTIME_END_STATIC_FRAMES = 12
REALTIME_START_MOTION = 0.004
REALTIME_HOLD_MOTION = 0.0015
REALTIME_INFER_STRIDE = 3
REALTIME_MAX_SEGMENT_FRAMES = FRAMES_PER_SAMPLE * 2
DISPLAY_HOLD_FRAMES = 12
HAND_FEATURE_SLICE = slice(-126, None)
DISPLAY_TOP_K = 6
TEMPORAL_VIEW_WINDOWS = (
    (0.0, 1.0),
    (0.05, 0.95),
    (0.1, 0.9),
    (0.15, 0.85),
    (0.2, 0.8),
)

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


def draw_confidence(img, classes, probs, W, H, display_label=None, display_confidence=None, top_k=DISPLAY_TOP_K):
    """Draw confidence bars for the strongest predictions + prediction overlay."""
    n = len(classes)
    if not n:
        return

    top_k = max(1, min(top_k, n))
    ranked = np.argsort(probs)[::-1][:top_k]

    # Panel
    pw, bh, gap, pad = 280, 22, 6, 15
    ph = pad*2 + top_k*(bh+gap) + 50
    px, py = W-pw-15, H-ph-15

    ov = img.copy()
    cv2.rectangle(ov, (px,py), (px+pw,py+ph), (30,30,30), -1)
    cv2.addWeighted(ov, 0.75, img, 0.25, 0, img)
    cv2.rectangle(img, (px,py), (px+pw,py+ph), (80,80,80), 1)
    cv2.putText(img, f"TOP {top_k} PREDICTIONS", (px+pad,py+25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)

    mbw = pw - 2*pad - 62

    for row, class_idx in enumerate(ranked):
        name = classes[class_idx]
        p = float(probs[class_idx])
        y = py + 45 + row*(bh+gap)
        col = BAR_COLORS[row % len(BAR_COLORS)]
        bx = px + pad + 62
        cv2.putText(img, name[:8], (px+pad, y+bh-6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)
        cv2.rectangle(img, (bx,y), (bx+mbw,y+bh), (60,60,60), -1)
        fw = int(mbw * p)
        if fw > 0: cv2.rectangle(img, (bx,y), (bx+fw,y+bh), col, -1)
        cv2.putText(img, f"{p*100:.0f}%", (bx+fw+4,y+bh-5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200,200,200), 1)

    # Big prediction
    if display_label is not None and display_confidence is not None:
        idx = classes.index(display_label) if display_label in classes else 0
        txt = f"{display_label} ({display_confidence*100:.1f}%)"
        col = BAR_COLORS[idx % len(BAR_COLORS)]
        sz = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
        ov2 = img.copy()
        cv2.rectangle(ov2, (10,10), (10+sz[0]+20, 10+sz[1]+20), (20,20,20), -1)
        cv2.addWeighted(ov2, 0.7, img, 0.3, 0, img)
        cv2.putText(img, txt, (20, 10+sz[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, col, 3)
    else:
        cv2.putText(img, "...", (20,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (120,120,120), 2)


def _resolve_live_prediction(history, classes, idle_label, min_confidence, stable_count):
    """Return a stable label/confidence once recent predictions agree."""
    accepted = [(idx, conf) for idx, conf in history if idx is not None and conf >= min_confidence]
    if len(accepted) < stable_count:
        return None, None

    idx_counts = Counter(idx for idx, _ in accepted)
    best_idx, best_count = idx_counts.most_common(1)[0]
    if best_count < stable_count:
        return None, None

    last_idx, last_conf = accepted[-1]
    if last_idx != best_idx:
        return None, None

    label = classes[best_idx]
    if idle_label and label == idle_label:
        return None, last_conf
    return label, last_conf


def _resample_sequence(sequence, target_len):
    """Resample a variable-length active segment to the model's fixed sequence length."""
    seq = np.asarray(sequence, dtype=np.float32)
    if len(seq) == 0:
        return np.zeros((target_len, 0), dtype=np.float32)
    if len(seq) == target_len:
        return seq
    if len(seq) == 1:
        return np.repeat(seq, target_len, axis=0)

    positions = np.linspace(0, len(seq) - 1, num=target_len, dtype=np.float32)
    lower = np.floor(positions).astype(int)
    upper = np.ceil(positions).astype(int)
    alpha = (positions - lower).reshape(-1, 1).astype(np.float32)
    return seq[lower] * (1.0 - alpha) + seq[upper] * alpha


def _crop_sequence(sequence, start_ratio, end_ratio):
    """Crop the active segment to reduce preparation / recovery frames."""
    seq = np.asarray(sequence, dtype=np.float32)
    if len(seq) == 0:
        return seq
    start = max(0, min(len(seq) - 1, int(np.floor(len(seq) * start_ratio))))
    end = max(start + 1, min(len(seq), int(np.ceil(len(seq) * end_ratio))))
    return seq[start:end]


def _predict_temporal_views(model, sequence, seq_len, scaler, idle_label, classes):
    """Choose a stronger final prediction by checking a few temporal crops."""
    outputs = []
    idle_idx = classes.index(idle_label) if idle_label in classes else None

    for start_ratio, end_ratio in TEMPORAL_VIEW_WINDOWS:
        cropped = _crop_sequence(sequence, start_ratio, end_ratio)
        if len(cropped) == 0:
            continue
        seq = _resample_sequence(cropped, seq_len)
        seq = apply_feature_scaler(seq, scaler)
        probs = model.predict(np.expand_dims(seq, 0), verbose=0)[0]
        top_idx = int(np.argmax(probs))
        top_conf = float(probs[top_idx])
        is_idle_top1 = idle_idx is not None and top_idx == idle_idx
        non_idle_conf = top_conf
        if idle_idx is not None and len(probs) > 1:
            masked = np.asarray(probs, dtype=np.float32).copy()
            masked[idle_idx] = -1.0
            non_idle_conf = float(np.max(masked))
        outputs.append({
            "probs": probs,
            "top_idx": top_idx,
            "top_conf": top_conf,
            "is_idle_top1": is_idle_top1,
            "non_idle_conf": non_idle_conf,
        })

    if not outputs:
        return None

    selected = outputs[0]
    if selected["is_idle_top1"]:
        selected = max(
            outputs,
            key=lambda item: (
                0 if item["is_idle_top1"] else 1,
                item["non_idle_conf"],
                item["top_conf"],
            ),
        )
    return selected["probs"]


def _hand_motion_score(previous_keypoints, current_keypoints):
    """Estimate short-term hand motion from the hand feature slice only."""
    if previous_keypoints is None:
        return 0.0
    prev_hands = np.asarray(previous_keypoints, dtype=np.float32)[HAND_FEATURE_SLICE]
    curr_hands = np.asarray(current_keypoints, dtype=np.float32)[HAND_FEATURE_SLICE]
    if prev_hands.size == 0 or curr_hands.size == 0:
        return 0.0
    diff = curr_hands - prev_hands
    return float(np.linalg.norm(diff) / np.sqrt(diff.size))


def run(model_path=None, device="auto", gpu_index=None,
        min_confidence=MIN_CONFIDENCE,
        stability_window=PREDICTION_SMOOTHING_WINDOW,
        stable_count=STABLE_PREDICTION_COUNT,
        min_active_frames=REALTIME_MIN_ACTIVE_FRAMES,
        end_static_frames=REALTIME_END_STATIC_FRAMES,
        start_motion=REALTIME_START_MOTION,
        hold_motion=REALTIME_HOLD_MOTION,
        infer_stride=REALTIME_INFER_STRIDE,
        top_k=DISPLAY_TOP_K):
    device_info = configure_tensorflow_runtime(device=device, gpu_index=gpu_index)
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
    scaler = load_feature_scaler()
    idle_label = find_idle_label(classes)
    active_preds = deque(maxlen=max(stability_window, stable_count))

    print(f"Model: {model_path}")
    print(f"Classes: {classes} | Buffer: {seq_len} frames")
    print(f"Live threshold: {min_confidence:.2f} | Stability window: {stability_window} | Stable count: {stable_count}")
    print(
        f"Realtime gating: min_active={min_active_frames} | end_static={end_static_frames} | "
        f"start_motion={start_motion:.4f} | hold_motion={hold_motion:.4f} | infer_stride={infer_stride}"
    )
    if idle_label:
        print(f"Idle/background class: {idle_label}")
    else:
        print("Warning: no idle/no-sign class found. Background frames may still map to a sign.")
    if scaler:
        print("Feature standardization: loaded from saved_models/feature_scaler.npz")

    pose_lm, hand_lm, face_lm = create_landmarkers()
    ts = 0

    cam = cv2.VideoCapture(0)
    if not cam.isOpened(): print("No webcam."); return
    W = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print("Press 'q' to quit\n")
    pre_roll = deque(maxlen=REALTIME_PRE_ROLL_FRAMES)
    segment_frames = []
    segment_hands = []
    last_probs = np.zeros(len(classes), dtype=np.float32)
    display_label = None
    display_conf = None
    display_hold = 0
    segment_announced_label = None
    segment_active = False
    static_frames = 0
    frames_since_infer = 0
    cooldown_frames = 0
    prev_keypoints = None

    while cam.isOpened():
        ok, frame = cam.read()
        if not ok: break

        ts += 33
        pose_r, hand_r, face_r = detect_landmarks(pose_lm, hand_lm, face_lm, frame, ts)

        d = frame.copy()
        draw_landmarks(d, pose_r, hand_r, face_r)
        hands_now = count_detected_hands(hand_r)
        keypoints = extract_keypoints(pose_r, hand_r, face_r)
        motion_score = _hand_motion_score(prev_keypoints, keypoints)
        prev_keypoints = keypoints
        pre_roll.append((keypoints, 1 if hands_now else 0))

        if cooldown_frames > 0:
            cooldown_frames -= 1

        started_now = False
        if (not segment_active and cooldown_frames == 0 and hands_now > 0 and motion_score >= start_motion):
            segment_active = True
            segment_frames = [item[0] for item in pre_roll]
            segment_hands = [item[1] for item in pre_roll]
            active_preds.clear()
            segment_announced_label = None
            static_frames = 0
            frames_since_infer = 0
            started_now = True

        if segment_active and not started_now:
            segment_frames.append(keypoints)
            segment_hands.append(1 if hands_now else 0)

        if segment_active:
            if len(segment_frames) > REALTIME_MAX_SEGMENT_FRAMES:
                segment_frames = segment_frames[-REALTIME_MAX_SEGMENT_FRAMES:]
                segment_hands = segment_hands[-REALTIME_MAX_SEGMENT_FRAMES:]

            if motion_score >= hold_motion:
                static_frames = 0
            else:
                static_frames += 1

            frames_since_infer += 1
            should_infer = (
                len(segment_frames) >= min_active_frames and
                (frames_since_infer == 1 or frames_since_infer % infer_stride == 0 or static_frames >= end_static_frames)
            )

            if should_infer:
                start_time = time.time()
                seq = _resample_sequence(segment_frames, seq_len)
                seq = apply_feature_scaler(seq, scaler)
                pred = model.predict(np.expand_dims(seq, 0), verbose=0)[0]
                latency = (time.time() - start_time) * 1000  # ms
                last_probs = pred

                top_idx = int(np.argmax(pred))
                top_conf = float(pred[top_idx])
                active_preds.append((top_idx, top_conf))

                hand_ratio = sum(segment_hands) / len(segment_hands) if segment_hands else 0.0
                stable_label, stable_conf = _resolve_live_prediction(
                    active_preds, classes, idle_label, min_confidence, stable_count)
                if stable_label and hand_ratio < MIN_SIGN_HAND_VISIBILITY_RATIO:
                    stable_label, stable_conf = None, None

                if stable_label:
                    display_label = stable_label
                    display_conf = stable_conf
                    display_hold = DISPLAY_HOLD_FRAMES
                    if segment_announced_label != stable_label:
                        print(f"[LIVE EVAL] Prediction: {stable_label} | Confidence: {stable_conf:.4f} | Latency: {latency:.2f}ms")
                        segment_announced_label = stable_label

                if static_frames >= end_static_frames:
                    refined_probs = _predict_temporal_views(model, segment_frames, seq_len, scaler, idle_label, classes)
                    if refined_probs is not None:
                        last_probs = refined_probs
                        refined_idx = int(np.argmax(refined_probs))
                        refined_label = classes[refined_idx]
                        refined_conf = float(refined_probs[refined_idx])
                        if not idle_label or refined_label != idle_label:
                            display_label = refined_label
                            display_conf = refined_conf
                            display_hold = DISPLAY_HOLD_FRAMES
                            if segment_announced_label != refined_label:
                                print(f"[LIVE FINAL] Prediction: {refined_label} | Confidence: {refined_conf:.4f}")
                                segment_announced_label = refined_label

                    segment_active = False
                    segment_frames = []
                    segment_hands = []
                    active_preds.clear()
                    static_frames = 0
                    frames_since_infer = 0
                    cooldown_frames = REALTIME_PRE_ROLL_FRAMES
        else:
            cv2.putText(d, "Waiting for sign", (20,50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,200,255), 2)

        if display_hold > 0:
            show_label = display_label
            show_conf = display_conf
            display_hold -= 1
        else:
            show_label = display_label if segment_active else None
            show_conf = display_conf if segment_active else None
            if not segment_active:
                display_label = None
                display_conf = None

        draw_confidence(d, classes, last_probs, W, H, show_label, show_conf, top_k=top_k)
        state = "SIGNING" if segment_active else ("COOLDOWN" if cooldown_frames > 0 else "IDLE")
        hand_ratio = sum(segment_hands) / len(segment_hands) if segment_hands else 0.0
        cv2.putText(d, f"State: {state}", (20, 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180,220,255), 2)
        cv2.putText(d, f"Motion: {motion_score:.4f} | Segment: {len(segment_frames)}f | Hands: {hand_ratio*100:.0f}%",
                    (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,220,255), 2)

        cv2.imshow("RSL Live Tester", d)
        if cv2.waitKey(1) & 0xFF == ord("q"): break

    close_landmarkers(pose_lm, hand_lm, face_lm)
    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="RSL Live Tester")
    p.add_argument("--model", "-m", type=str, default=None)
    p.add_argument("--device", choices=["auto", "gpu", "cpu"], default="auto")
    p.add_argument("--gpu-index", type=int, default=None)
    p.add_argument("--confidence", type=float, default=MIN_CONFIDENCE)
    p.add_argument("--stability-window", type=int, default=PREDICTION_SMOOTHING_WINDOW)
    p.add_argument("--stable-count", type=int, default=STABLE_PREDICTION_COUNT)
    p.add_argument("--min-active-frames", type=int, default=REALTIME_MIN_ACTIVE_FRAMES)
    p.add_argument("--end-static-frames", type=int, default=REALTIME_END_STATIC_FRAMES)
    p.add_argument("--start-motion", type=float, default=REALTIME_START_MOTION)
    p.add_argument("--hold-motion", type=float, default=REALTIME_HOLD_MOTION)
    p.add_argument("--infer-stride", type=int, default=REALTIME_INFER_STRIDE)
    p.add_argument("--top-k", type=int, default=DISPLAY_TOP_K)
    p.add_argument("--list-devices", action="store_true")
    a = p.parse_args()
    if a.list_devices:
        list_tensorflow_devices()
    else:
        run(
            a.model,
            a.device,
            a.gpu_index,
            a.confidence,
            a.stability_window,
            a.stable_count,
            a.min_active_frames,
            a.end_static_frames,
            a.start_motion,
            a.hold_motion,
            a.infer_stride,
            a.top_k,
        )
