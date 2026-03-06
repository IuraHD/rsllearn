# Mermaid Diagram Sources

All diagram source code for the RSL Dataset Toolkit documentation.
Run `python render_diagrams.py` to regenerate the JPEG images.

---

## 01 — Architecture Overview

```mermaid
graph TB
    subgraph RSL_Dataset_Toolkit[RSL Dataset Toolkit]
        direction TB
        U["utils.py<br/>Shared Module"]
        C["rsl_data_collector.py<br/>Recording"]
        T["rsl_model_trainer.py<br/>Training"]
        L["rsl_testare_live.py<br/>Live Inference"]
        C --> U
        T --> U
        L --> U
    end
    subgraph External[External Dependencies]
        MP["MediaPipe Tasks API<br/>Pose + Hand + Face"]
        TF["TensorFlow / Keras<br/>LSTM Model"]
        CV["OpenCV<br/>Webcam + Display"]
    end
    U --> MP
    U --> CV
    T --> TF
    L --> TF
    subgraph Storage
        LM["dataset/landmarks/ .npy"]
        CL["dataset/clips/ .mp4"]
        SM["saved_models/ .h5"]
        MM["mp_models/ .task"]
    end
    C --> LM
    C --> CL
    T --> LM
    T --> SM
    L --> SM
    U --> MM
    style U fill:#4a90d9,stroke:#2c5f8a,color:#fff
    style C fill:#27ae60,stroke:#1e8449,color:#fff
    style T fill:#e67e22,stroke:#ca6f1e,color:#fff
    style L fill:#8e44ad,stroke:#6c3483,color:#fff
```

---

## 02 — System Pipeline

```mermaid
flowchart LR
    A["📹 Webcam<br/>30 FPS"] --> B["🤖 MediaPipe<br/>3 Landmarkers"]
    B --> C["📊 Extract<br/>Keypoints"]
    C --> D["💾 Save .npy"]
    D --> E["📥 Load<br/>Sequences"]
    E --> F["🔀 Augment"]
    F --> G["🧠 Train<br/>LSTM"]
    G --> H["💾 Save .h5"]
    H --> I["📹 Live<br/>Webcam"]
    I --> J["🤖 Detect"]
    J --> K["🧠 Predict"]
    K --> L["📊 Confidence<br/>Bars"]
    style A fill:#2ecc71,color:#fff
    style B fill:#3498db,color:#fff
    style C fill:#3498db,color:#fff
    style D fill:#f39c12,color:#fff
    style E fill:#e67e22,color:#fff
    style F fill:#e67e22,color:#fff
    style G fill:#e74c3c,color:#fff
    style H fill:#f39c12,color:#fff
    style I fill:#9b59b6,color:#fff
    style J fill:#9b59b6,color:#fff
    style K fill:#9b59b6,color:#fff
    style L fill:#9b59b6,color:#fff
```

---

## 03 — Class Diagram

```mermaid
classDiagram
    class utils {
        +PROJECT_DIR str
        +DATASET_FOLDER str
        +LANDMARKS_FOLDER str
        +CLIPS_FOLDER str
        +SAVED_MODELS_FOLDER str
        +MP_MODELS_FOLDER str
        +SAMPLES_PER_SIGN int = 30
        +FRAMES_PER_SAMPLE int = 90
        +FACE_KEY_INDICES list~int~
        +NUM_FACE_KEY int = 68
        +TOTAL_FEATURES int = 429
        +POSE_CONNECTIONS list
        +HAND_CONNECTIONS list
        +ensure_models()
        +create_landmarkers(mode) tuple
        +close_landmarkers(pose, hands, face)
        +detect_landmarks(pose_lm, hand_lm, face_lm, frame, timestamp_ms) tuple
        +extract_keypoints(pose_res, hand_res, face_res) ndarray
        +draw_landmarks(image, pose_res, hand_res, face_res)
    }
    class rsl_data_collector {
        +find_next_seq(folder, name) int
        +ask_words() list~str~
        +collect(word_list, num_samples, num_frames)
    }
    class rsl_model_trainer {
        +MAX_EPOCHS int = 200
        +BATCH_SIZE int = 32
        +VAL_SPLIT float = 0.15
        +TEST_SPLIT float = 0.15
        +PATIENCE int = 20
        +NOISE float = 0.01
        -_read_feature_size() int
        -_read_seq_length() int
        +load_data(classes, seq_len) tuple
        +augment(X, y) tuple
        +train(epochs, do_augment, patience) Model
    }
    class rsl_testare_live {
        +MIN_CONFIDENCE float = 0.5
        +BAR_COLORS list
        -_load_classes() list~str~
        -_load_seq_len() int
        +draw_confidence(img, classes, probs, W, H)
        +run(model_path)
    }
    rsl_data_collector --> utils : imports
    rsl_model_trainer --> utils : imports
    rsl_testare_live --> utils : imports
```

---

## 04 — Feature Vector Breakdown

```mermaid
pie title Feature Vector Breakdown (429 total)
    "Pose 33×3 = 99" : 99
    "Face Key 68×3 = 204" : 204
    "Left Hand 21×3 = 63" : 63
    "Right Hand 21×3 = 63" : 63
```

---

## 05 — Data Collection Sequence

```mermaid
sequenceDiagram
    participant User
    participant Collector
    participant MediaPipe
    participant FileSystem
    User->>Collector: Enter words
    loop For each word
        Collector->>Collector: Countdown (orange border)
        loop For each sequence (30x)
            loop 90 frames (~3 sec)
                Collector->>MediaPipe: detect_for_video()
                MediaPipe-->>Collector: landmarks
                Collector->>Collector: extract 429 features
            end
            Collector->>FileSystem: Save .npy (90×429)
            Collector->>FileSystem: Save .mp4 backup
        end
    end
```

---

## 06 — Training Sequence

```mermaid
sequenceDiagram
    participant FS as FileSystem
    participant Trainer
    participant LSTM as LSTM Model
    Trainer->>FS: Discover classes
    Trainer->>FS: Load .npy files
    Trainer->>Trainer: Augment (noise + shift)
    Trainer->>Trainer: Split 70/15/15 (train/val/test)
    Trainer->>LSTM: Build 3-layer LSTM
    Trainer->>LSTM: Train with callbacks (val set)
    LSTM-->>Trainer: Best weights
    Trainer->>Trainer: Evaluate on held-out test set
    Trainer->>FS: Save model + classes
```

---

## 07 — Live Test Sequence

```mermaid
sequenceDiagram
    participant Cam as Webcam
    participant Tester
    participant MP as MediaPipe
    participant Model as LSTM
    Tester->>Model: Load model
    loop Every frame
        Cam->>Tester: Read frame
        Tester->>MP: detect_for_video()
        MP-->>Tester: Landmarks
        Tester->>Tester: Buffer keypoints
        alt Buffer full (90 frames)
            Tester->>Model: predict()
            Model-->>Tester: Probabilities
            Tester->>Tester: Draw confidence bars
        end
    end
```

---

## 08 — State Machine

```mermaid
stateDiagram-v2
    [*] --> Setup : Start script
    Setup --> WordInput
    WordInput --> Countdown : Words entered
    Countdown --> Recording : 3..2..1
    Recording --> Saving : 90 frames done
    Recording --> Skipped : press S
    Recording --> Redo : press R
    Recording --> Quit : press Q
    Saving --> Pause : saved .npy + .mp4
    Pause --> Recording : next sequence
    Pause --> Countdown : next word
    Skipped --> Recording
    Redo --> Recording
    Countdown --> [*] : all words done
    Quit --> [*]
```

---

## 09 — Model Architecture

```mermaid
graph TB
    I["Input<br/>90 × 429"] --> L1["LSTM 64<br/>return_sequences"]
    L1 --> D1["Dropout 0.2"]
    D1 --> L2["LSTM 128<br/>return_sequences"]
    L2 --> D2["Dropout 0.2"]
    D2 --> L3["LSTM 64"]
    L3 --> D3["Dropout 0.2"]
    D3 --> F1["Dense 64 ReLU"]
    F1 --> D4["Dropout 0.2"]
    D4 --> F2["Dense 32 ReLU"]
    F2 --> O["Dense N Softmax<br/>N = num signs"]
    style I fill:#3498db,color:#fff
    style L1 fill:#e74c3c,color:#fff
    style L2 fill:#e74c3c,color:#fff
    style L3 fill:#e74c3c,color:#fff
    style F1 fill:#2ecc71,color:#fff
    style F2 fill:#2ecc71,color:#fff
    style O fill:#f39c12,color:#fff
    style D1 fill:#95a5a6,color:#fff
    style D2 fill:#95a5a6,color:#fff
    style D3 fill:#95a5a6,color:#fff
    style D4 fill:#95a5a6,color:#fff
```
