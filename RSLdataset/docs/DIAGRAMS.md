# Mermaid Diagram Sources

All diagram source code for the RSL Dataset Toolkit documentation.
Run `python render_diagrams.py` to regenerate the JPEG images.

---

## 01 — Architecture Overview

```mermaid
graph TB
    subgraph Toolkit["RSL Dataset Toolkit"]
        direction TB
        U["utils.py<br/>Shared paths, MediaPipe, TensorFlow, scaler helpers"]
        C["rsl_data_collector.py<br/>Dataset recording"]
        T["rsl_model_trainer.py<br/>Training + evaluation export"]
        L["rsl_testare_live.py<br/>Realtime segmented inference"]
        C --> U
        T --> U
        L --> U
    end

    subgraph External["External Dependencies"]
        MP["MediaPipe Tasks<br/>Pose + Hands + Face"]
        TF["TensorFlow / Keras<br/>RNN(LSTMCell) classifier"]
        CV["OpenCV<br/>Webcam + overlays"]
        SK["NumPy / scikit-learn / pandas / matplotlib"]
    end

    subgraph Storage["Project Storage"]
        LM["dataset/landmarks/<br/>class folders + _metadata.txt"]
        CL["dataset/clips/<br/>backup .mp4 clips"]
        SM["saved_models/<br/>best_model.h5, rsl_*.h5,<br/>sign_classes.txt, model_meta.txt,<br/>feature_scaler.npz"]
        EV["evaluation_outputs/<br/>JSON, CSV, PNG, Markdown report"]
        MM["mp_models/<br/>.task files"]
    end

    U --> MP
    U --> CV
    U --> TF
    T --> SK

    C --> LM
    C --> CL
    C --> MM
    T --> LM
    T --> SM
    T --> EV
    L --> SM
    L --> MM

    style U fill:#4a90d9,stroke:#2c5f8a,color:#fff
    style C fill:#27ae60,stroke:#1e8449,color:#fff
    style T fill:#e67e22,stroke:#ca6f1e,color:#fff
    style L fill:#8e44ad,stroke:#6c3483,color:#fff
```

---

## 02 — System Pipeline

```mermaid
flowchart LR
    A["Webcam frame stream"] --> B["MediaPipe VIDEO mode<br/>pose + hands + face"]
    B --> C["Extract 429 landmark features<br/>33 pose + 68 face + 21 + 21 hands"]
    C --> D["Collector saves<br/>.npy sequence + .mp4 clip + metadata"]
    D --> E["Trainer loads class folders<br/>and reads seq_len / feature size"]
    E --> F["Stratified split<br/>train / val / held-out test"]
    F --> G["Optional train-only augmentation<br/>spatial + temporal + combined"]
    G --> H["Fit feature scaler on raw train split"]
    H --> I["Standardize train / val / test"]
    I --> J["Train RNN(LSTMCell) stack<br/>checkpoint + early stop + LR reduction"]
    J --> K["Save model artifacts<br/>model, classes, scaler, metadata"]
    J --> L["Export evaluation outputs<br/>metrics, report, plots, confusion matrix"]
    K --> M["Live webcam inference"]
    M --> N["Motion-gated active segment detection<br/>pre-roll + hand visibility"]
    N --> O["Resample segment to fixed length<br/>then apply saved scaler"]
    O --> P["Predict class probabilities"]
    P --> Q["Stability filter + idle suppression<br/>confidence bars + label overlay"]

    style A fill:#2ecc71,color:#fff
    style B fill:#3498db,color:#fff
    style C fill:#3498db,color:#fff
    style D fill:#f39c12,color:#fff
    style E fill:#e67e22,color:#fff
    style F fill:#e67e22,color:#fff
    style G fill:#e67e22,color:#fff
    style H fill:#e67e22,color:#fff
    style I fill:#e67e22,color:#fff
    style J fill:#e74c3c,color:#fff
    style K fill:#f39c12,color:#fff
    style L fill:#f39c12,color:#fff
    style M fill:#9b59b6,color:#fff
    style N fill:#9b59b6,color:#fff
    style O fill:#9b59b6,color:#fff
    style P fill:#9b59b6,color:#fff
    style Q fill:#9b59b6,color:#fff
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
        +FEATURE_SCALER_FILE str
        +SAMPLES_PER_SIGN int = 60
        +FRAMES_PER_SAMPLE int = 60
        +TOTAL_FEATURES int = 429
        +DEFAULT_MIN_CONFIDENCE float = 0.8
        +PREDICTION_SMOOTHING_WINDOW int = 5
        +STABLE_PREDICTION_COUNT int = 3
        +MIN_SIGN_HAND_VISIBILITY_RATIO float = 0.2
        +normalize_label_name(name) str
        +is_idle_label(name) bool
        +find_idle_label(classes) str
        +count_detected_hands(hand_res) int
        +fit_feature_scaler(X) dict
        +apply_feature_scaler(X, scaler) ndarray
        +save_feature_scaler(scaler, path) None
        +load_feature_scaler(path) dict
        +configure_tensorflow_runtime(device, gpu_index) dict
        +list_tensorflow_devices() dict
        +ensure_models() None
        +create_landmarkers(mode) tuple
        +close_landmarkers(pose, hands, face) None
        +detect_landmarks(pose_lm, hand_lm, face_lm, frame, timestamp_ms) tuple
        +extract_keypoints(pose_res, hand_res, face_res) ndarray
        +draw_landmarks(image, pose_res, hand_res, face_res) None
    }

    class rsl_data_collector {
        +find_next_seq(folder, name) int
        +ask_words() list~str~
        +wait_for_word_start(cam, word, word_index, total_words, total_samples) str
        +collect(word_list, num_samples, num_frames) None
    }

    class rsl_model_trainer {
        +MAX_EPOCHS int = 200
        +BATCH_SIZE int = 32
        +VAL_SPLIT float = 0.15
        +TEST_SPLIT float = 0.15
        +PATIENCE int = 20
        +AUGMENT_COPIES_PER_SAMPLE int = 3
        -_read_feature_size() int
        -_read_seq_length() int
        +load_data(classes, seq_len, max_samples_per_class) tuple
        +augment(X, y) tuple
        +train(epochs, do_augment, patience, device, gpu_index, max_samples_per_class) Model
    }

    class rsl_testare_live {
        +MIN_CONFIDENCE float
        +BAR_COLORS list
        +REALTIME_PRE_ROLL_FRAMES int = 8
        +REALTIME_MIN_ACTIVE_FRAMES int = 18
        +REALTIME_END_STATIC_FRAMES int = 12
        +REALTIME_INFER_STRIDE int = 3
        -_load_classes() list~str~
        -_load_seq_len() int
        -_resolve_live_prediction(history, classes, idle_label, min_confidence, stable_count) tuple
        -_resample_sequence(sequence, target_len) ndarray
        -_hand_motion_score(previous_keypoints, current_keypoints) float
        +draw_confidence(img, classes, probs, W, H, display_label, display_confidence) None
        +run(model_path, device, gpu_index, min_confidence, stability_window, stable_count, min_active_frames, end_static_frames, start_motion, hold_motion, infer_stride) None
    }

    rsl_data_collector --> utils : imports
    rsl_model_trainer --> utils : imports
    rsl_testare_live --> utils : imports
```

---

## 04 — Feature Vector Breakdown

```mermaid
pie title Feature Vector Breakdown (429 total)
    "Pose 33x3 = 99" : 99
    "Face key 68x3 = 204" : 204
    "Left hand 21x3 = 63" : 63
    "Right hand 21x3 = 63" : 63
```

---

## 05 — Data Collection Sequence

```mermaid
sequenceDiagram
    participant User
    participant Collector
    participant MediaPipe
    participant FileSystem

    User->>Collector: Enter sign labels
    Collector->>Collector: Define recording plan<br/>60 samples per sign

    loop For each word
        Collector->>User: Preview and 3-second countdown

        loop For each sample
            loop 60 frames (~2 seconds at 30 FPS)
                Collector->>MediaPipe: Detect pose, face, and hands
                MediaPipe-->>Collector: Landmark results
                Collector->>Collector: Extract 429 features per frame
            end

            Collector->>Collector: Validate captured sequence
            alt Sequence accepted
                Collector->>FileSystem: Save landmark sequence (.npy)
                Collector->>FileSystem: Save backup clip (.mp4)
            else Sequence rejected or repeated
                Collector->>Collector: Re-record sample
            end
        end
    end

    Collector->>FileSystem: Write metadata<br/>feature size and sequence length
```

---

## 06 — Training Sequence

```mermaid
sequenceDiagram
    participant FS as FileSystem
    participant Trainer
    participant Scaler
    participant Model as RNN(LSTMCell)

    Trainer->>FS: Read dataset and metadata
    Trainer->>Trainer: Build labelled sequence set
    Trainer->>Trainer: Stratified split<br/>70% train / 15% validation / 15% test
    Trainer->>Scaler: Fit scaler on raw training split only
    alt Augmentation enabled
        Trainer->>Trainer: Add one spatial, one temporal,<br/>and one combined copy per training sample
    end
    Trainer->>Scaler: Standardize train, validation, and test data
    Trainer->>Model: Train recurrent sequence model
    Model-->>Trainer: Best trained model
    Trainer->>Model: Evaluate on held-out test set
    Trainer->>FS: Save model, class list, scaler, and metadata
    Trainer->>FS: Export evaluation tables, plots, and report
```

---

## 07 — Live Test Sequence

```mermaid
sequenceDiagram
    participant Cam as Webcam
    participant Tester
    participant MP as MediaPipe
    participant Scaler
    participant Model as Trained Model

    Tester->>Model: Load trained model
    Tester->>Tester: Load class labels and sequence length
    Tester->>Scaler: Load saved feature scaler

    loop Every frame
        Cam->>Tester: Read frame
        Tester->>MP: detect_for_video()
        MP-->>Tester: Landmarks
        Tester->>Tester: Extract 429-feature vector
        Tester->>Tester: Update pre-roll buffer

        alt Sign activity detected
            Tester->>Tester: Start active segment
        end

        alt Segment active
            Tester->>Tester: Grow active segment from buffered frames
            Tester->>Tester: Resample to fixed sequence length
            Tester->>Scaler: Apply saved standardization
            Tester->>Model: Predict sign probabilities
            Model-->>Tester: Probability scores
            Tester->>Tester: Apply confidence and stability filtering
            Tester->>Tester: Suppress idle / no-sign output
            Tester->>Tester: End segment and enter cooldown
        end

        Tester->>Tester: Draw prediction overlay
    end
```

---

## 08 — Collector State Machine

```mermaid
stateDiagram-v2
    [*] --> Setup : Start script
    Setup --> WordInput : Initialize MediaPipe + webcam
    WordInput --> WordPreview : Labels entered
    WordPreview --> Countdown : Press Enter
    WordPreview --> Quit : Press q
    Countdown --> Recording : 3..2..1

    Recording --> SkipSample : Press s
    Recording --> RedoSample : Press r
    Recording --> Quit : Press q
    Recording --> RejectSample : Too few hand-visible frames
    Recording --> SaveSample : Valid sequence captured

    SkipSample --> Recording : Next sequence id
    RedoSample --> Recording : Repeat same sequence id
    RejectSample --> Recording : Repeat same sequence id
    SaveSample --> Pause : Keep .npy + .mp4

    Pause --> Recording : More samples for same word
    Pause --> WordPreview : Next word
    Pause --> Finalize : All words complete

    Finalize --> [*] : Write _metadata.txt and close resources
    Quit --> [*]
```

---

## 09 — Model Architecture

```mermaid
graph TB
    I["Standardized Input<br/>seq_len x feature_size<br/>default 60 x 429"] --> L1["RNN(LSTMCell 64)<br/>return_sequences"]
    L1 --> D1["Dropout 0.2"]
    D1 --> L2["RNN(LSTMCell 128)<br/>return_sequences"]
    L2 --> D2["Dropout 0.2"]
    D2 --> L3["RNN(LSTMCell 64)"]
    L3 --> D3["Dropout 0.2"]
    D3 --> F1["Dense 64 ReLU"]
    F1 --> D4["Dropout 0.2"]
    D4 --> F2["Dense 32 ReLU"]
    F2 --> O["Dense N Softmax<br/>N = number of classes"]

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
