"""
RSL Data Collector — Record sign language gestures via webcam.
Workflow: enter word count → type words → record each one.

Usage:
    python rsl_data_collector.py
    python rsl_data_collector.py --samples 30 --frames 90
"""

import cv2
import numpy as np
import os
import time
import argparse
from utils import (
    LANDMARKS_FOLDER, CLIPS_FOLDER, SAMPLES_PER_SIGN, FRAMES_PER_SAMPLE,
    TOTAL_FEATURES, NUM_FACE_KEY,
    create_landmarkers, close_landmarkers, detect_landmarks,
    extract_keypoints, draw_landmarks,
)


def find_next_seq(folder, name):
    """Next sequence number based on existing .npy files."""
    if not os.path.exists(folder):
        return 1
    nums = []
    for f in os.listdir(folder):
        if f.startswith(name) and f.endswith(".npy"):
            try: nums.append(int(f.replace(f"{name}_", "").replace(".npy", "")))
            except ValueError: pass
    return max(nums) + 1 if nums else 1


def ask_words():
    """Prompt user for word count and word list."""
    print("=" * 60)
    print("  RSL DATA COLLECTOR")
    print(f"  Features: {TOTAL_FEATURES}  (Pose:99 Face:{NUM_FACE_KEY*3} Hands:126)")
    print("=" * 60)

    while True:
        try:
            n = int(input("\nHow many words to record? "))
            if n > 0: break
        except ValueError: pass
        print("  Enter a positive number.")

    words = []
    for i in range(n):
        while True:
            w = input(f"  Word {i+1}/{n}: ").strip()
            if w: words.append(w); break
    print(f"\n  Words: {words}\n")
    return words


def collect(word_list, num_samples=None, num_frames=None):
    """Main collection loop."""
    num_samples = num_samples or SAMPLES_PER_SIGN
    num_frames = num_frames or FRAMES_PER_SAMPLE
    os.makedirs(LANDMARKS_FOLDER, exist_ok=True)
    os.makedirs(CLIPS_FOLDER, exist_ok=True)

    print("Initializing MediaPipe (VIDEO mode)...")
    pose_lm, hand_lm, face_lm = create_landmarkers()
    ts = 0  # monotonic timestamp for VIDEO mode

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("ERROR: No webcam."); return

    W = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cam.get(cv2.CAP_PROP_FPS) or 30)
    if fps > 120: fps = 30

    print(f"  {len(word_list)} words | {num_samples} samples | {num_frames} frames (~{num_frames/fps:.1f}s)")
    print("  Controls: q=quit  s=skip  r=redo\n")

    stop = False
    for wi, word in enumerate(word_list):
        if stop: break
        lm_dir = os.path.join(LANDMARKS_FOLDER, word)
        vid_dir = os.path.join(CLIPS_FOLDER, word)
        os.makedirs(lm_dir, exist_ok=True)
        os.makedirs(vid_dir, exist_ok=True)
        seq = find_next_seq(lm_dir, word)

        print(f"[{wi+1}/{len(word_list)}] \"{word}\" — {num_samples} sequences from #{seq}")

        # Countdown — live camera, orange border
        for c in range(3, 0, -1):
            t_end = time.time() + 1.0
            while time.time() < t_end:
                ok, frame = cam.read()
                if not ok: break
                d = frame.copy()
                cv2.rectangle(d, (0,0), (W-1,H-1), (0,165,255), 6)
                cv2.putText(d, f"\"{word}\" in {c}...", (80, H//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,165,255), 3)
                cv2.imshow("RSL Data Collector", d)
                cv2.waitKey(1)

        done = 0
        while done < num_samples and not stop:
            vid_path = os.path.join(vid_dir, f"{word}_{seq}.mp4")
            writer = cv2.VideoWriter(vid_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
            kps, skip, redo = [], False, False

            for fi in range(num_frames):
                ok, frame = cam.read()
                if not ok: break
                writer.write(frame)

                ts += 33  # ~30fps timestamp increment
                pose_r, hand_r, face_r = detect_landmarks(pose_lm, hand_lm, face_lm, frame, ts)

                d = frame.copy()
                draw_landmarks(d, pose_r, hand_r, face_r)

                # Green border + REC
                cv2.rectangle(d, (0,0), (W-1,H-1), (0,200,0), 6)
                cv2.circle(d, (25,30), 8, (0,0,255), -1)
                cv2.putText(d, "REC", (40,38), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

                # Info
                cv2.rectangle(d, (80,5), (W-10,50), (40,40,40), -1)
                cv2.putText(d, f"\"{word}\" Seq {seq} | {fi+1}/{num_frames}",
                            (90,38), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 2)
                cv2.putText(d, f"[{wi+1}/{len(word_list)}]",
                            (W-110,38), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,255), 2)

                # Progress
                pct = fi / num_frames
                cv2.rectangle(d, (10,H-30), (W-10,H-10), (50,50,50), -1)
                cv2.rectangle(d, (10,H-30), (10+int((W-20)*pct),H-10), (0,200,0), -1)

                cv2.imshow("RSL Data Collector", d)
                kps.append(extract_keypoints(pose_r, hand_r, face_r))

                k = cv2.waitKey(1) & 0xFF
                if k == ord("q"): stop = True; break
                elif k == ord("s"): skip = True; break
                elif k == ord("r"): redo = True; break

            writer.release()

            if stop: break
            if skip or redo:
                if os.path.exists(vid_path): os.remove(vid_path)
                if skip: print(f"    >> Skipped {seq}"); seq += 1
                else: print(f"    >> Redo {seq}")
                continue

            np.save(os.path.join(lm_dir, f"{word}_{seq}.npy"), np.array(kps))
            done += 1; seq += 1
            print(f"    Saved ({done}/{num_samples})")

            # Pause — live camera, blue border
            if done < num_samples:
                t_end = time.time() + 2.0
                while time.time() < t_end and not stop:
                    ok, frame = cam.read()
                    if not ok: break
                    d = frame.copy()
                    cv2.rectangle(d, (0,0), (W-1,H-1), (255,165,0), 6)
                    cv2.putText(d, f"Next in {max(0,t_end-time.time()):.0f}s",
                                (80,H//2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,165,0), 2)
                    cv2.imshow("RSL Data Collector", d)
                    if cv2.waitKey(1) & 0xFF == ord("q"): stop = True

        print(f"  \"{word}\" done — {done} sequences")

    close_landmarkers(pose_lm, hand_lm, face_lm)
    cam.release()
    cv2.destroyAllWindows()

    # Metadata
    with open(os.path.join(LANDMARKS_FOLDER, "_metadata.txt"), "w") as f:
        f.write(f"features={TOTAL_FEATURES}\nframes={num_frames}\n")

    print(f"\nDone! Landmarks: {LANDMARKS_FOLDER}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="RSL Data Collector")
    p.add_argument("--samples", "-n", type=int, default=None)
    p.add_argument("--frames", "-f", type=int, default=None)
    a = p.parse_args()
    collect(ask_words(), a.samples, a.frames)
