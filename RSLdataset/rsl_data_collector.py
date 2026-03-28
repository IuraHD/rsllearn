"""
RSL Data Collector — Record sign language gestures via webcam.
Workflow: enter word count → type words → record each one.

Usage:
    python rsl_data_collector.py
    python rsl_data_collector.py --samples 60 --frames 60
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
    count_detected_hands, find_idle_label, MIN_SIGN_HAND_VISIBILITY_RATIO,
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

    print("\n  Enter the words as a single comma-separated list.")
    print("  Example: Salut, La revedere, Multumesc, idle")

    words = []
    while True:
        raw = input(f"\n  Paste {n} words separated by commas: ").strip()
        if not raw:
            print("  Enter at least one word.")
            continue

        parsed = [w.strip() for w in raw.split(",") if w.strip()]
        if len(parsed) != n:
            print(f"  Expected {n} words, but got {len(parsed)}. Please try again.")
            continue

        words = parsed
        break

    print(f"\n  Words: {words}\n")
    if not find_idle_label(words):
        print("  Recommendation: add an 'idle' label so live testing can learn no-sign/background frames.\n")
    return words


def wait_for_word_start(cam, word, word_index, total_words, total_samples):
    """Show a live preview and wait for Enter before starting a new word."""
    while True:
        ok, frame = cam.read()
        if not ok:
            return "quit"

        h, w = frame.shape[:2]
        d = frame.copy()
        cv2.rectangle(d, (0, 0), (w - 1, h - 1), (255, 200, 0), 6)
        cv2.rectangle(d, (35, 35), (w - 35, 175), (30, 30, 30), -1)

        cv2.putText(d, f"Word {word_index}/{total_words}", (55, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(d, f"\"{word}\"", (55, 115),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
        cv2.putText(d, f"Prepare for {total_samples} recordings", (55, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 255, 200), 2)

        cv2.putText(d, "Press Enter to start this word", (55, h - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
        cv2.putText(d, "Press q to quit", (55, h - 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 200, 255), 2)

        cv2.imshow("RSL Data Collector", d)
        k = cv2.waitKey(1) & 0xFF
        if k in (13, 10):
            return "start"
        if k == ord("q"):
            return "quit"


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

    idle_label = find_idle_label(word_list)

    print(f"  {len(word_list)} words | {num_samples} samples | {num_frames} frames (~{num_frames/fps:.1f}s)")
    print("  Recording guidance:")
    print("    - Keep the upper body and both hands inside the frame.")
    print("    - Start the sign quickly and keep it centered in the 2-second window.")
    print("    - Use stable lighting and a plain background when possible.")
    if not idle_label:
        print("    - Add an 'idle' label in the next recording pass to reduce live false positives.")
    print("  Controls: Enter=start word  q=quit  s=skip sample  r=redo sample\n")

    stop = False
    for wi, word in enumerate(word_list):
        if stop: break
        lm_dir = os.path.join(LANDMARKS_FOLDER, word)
        vid_dir = os.path.join(CLIPS_FOLDER, word)
        os.makedirs(lm_dir, exist_ok=True)
        os.makedirs(vid_dir, exist_ok=True)
        seq = find_next_seq(lm_dir, word)

        print(f"[{wi+1}/{len(word_list)}] \"{word}\" — {num_samples} sequences from #{seq}")

        start_action = wait_for_word_start(cam, word, wi + 1, len(word_list), num_samples)
        if start_action == "quit":
            stop = True
            break

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
            hand_visible_frames = 0

            for fi in range(num_frames):
                ok, frame = cam.read()
                if not ok: break
                writer.write(frame)

                ts += 33  # ~30fps timestamp increment
                pose_r, hand_r, face_r = detect_landmarks(pose_lm, hand_lm, face_lm, frame, ts)
                hands_now = count_detected_hands(hand_r)
                if hands_now:
                    hand_visible_frames += 1

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
                cv2.putText(d, f"Hands detected: {hands_now}", (90, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 255, 200), 1)

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

            min_hand_frames = max(1, int(num_frames * MIN_SIGN_HAND_VISIBILITY_RATIO))
            if word != idle_label and hand_visible_frames < min_hand_frames:
                if os.path.exists(vid_path): os.remove(vid_path)
                print(f"    >> Rejected {seq}: only {hand_visible_frames}/{num_frames} frames had hands visible.")
                print("       Redo the clip with hands kept in frame for more of the sign.")
                continue

            np.save(os.path.join(lm_dir, f"{word}_{seq}.npy"), np.array(kps))
            done += 1; seq += 1
            print(f"    Saved ({done}/{num_samples}) | hand-visible frames: {hand_visible_frames}/{num_frames}")

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
