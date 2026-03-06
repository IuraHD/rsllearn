# RSL Dataset Toolkit Documentation

This toolkit has three offline steps:

1. Record a dataset from webcam video.
2. Train the LSTM model on saved landmark sequences.
3. Run live inference/testing from webcam input.

There is no separate offline batch inference script in this toolkit.
For testing and inference, use `rsl_testare_live.py`.

## Toolkit Scripts

| Script | Purpose | Run when |
|---|---|---|
| `rsl_data_collector.py` | Record sign samples and save landmarks + video clips | You want to build or extend the dataset |
| `rsl_model_trainer.py` | Train the LSTM model on recorded `.npy` landmark sequences | You already collected data |
| `rsl_testare_live.py` | Run live inference/test from webcam using a trained `.h5` model | You want to test predictions in real time |
| `utils.py` | Shared constants and helper functions | Imported by the scripts above |

## Quick Start

Open PowerShell in the toolkit folder:

```powershell
cd C:\Users\IuraHD\Desktop\disertation\rsl\RSLdataset
```

Create and activate a virtual environment if needed:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If the environment already exists, only activate it and install requirements if needed.

## How To Run

### 1. Record the Dataset

Run:

```powershell
python rsl_data_collector.py
```

Optional custom settings:

```powershell
python rsl_data_collector.py --samples 40 --frames 90
```

What happens:

- The script asks how many words/signs you want to record.
- You type each word/sign label in the console.
- The webcam opens.
- For each word, the script records multiple sequences.
- It saves landmarks as `.npy` files and raw backup clips as `.mp4` files.

Collector controls:

- `q` = quit
- `s` = skip current sequence
- `r` = redo current sequence

Recorded data is saved to:

- `dataset\landmarks\<word>\*.npy`
- `dataset\clips\<word>\*.mp4`
- `dataset\landmarks\_metadata.txt`

### 2. Train the Model

Run:

```powershell
python rsl_model_trainer.py
```

Useful options:

```powershell
python rsl_model_trainer.py --epochs 300
python rsl_model_trainer.py --augment
python rsl_model_trainer.py --epochs 300 --augment --patience 30
```

What happens:

- The script loads the recorded landmark sequences from `dataset\landmarks`.
- It splits data into train, validation, and held-out test sets.
- It trains the LSTM model.
- It evaluates the final model on the held-out test set.
- It exports the trained model and evaluation files.

Training outputs:

- `saved_models\best_model.h5`
- `saved_models\rsl_YYYYMMDD_HHMM.h5`
- `saved_models\sign_classes.txt`
- `saved_models\model_meta.txt`
- `evaluation_outputs\metrics_summary.json`
- `evaluation_outputs\classification_report.csv`
- `evaluation_outputs\confusion_matrix.csv`
- `evaluation_outputs\confusion_matrix.png`
- `evaluation_outputs\training_history.png`
- `evaluation_outputs\class_distribution.csv`
- `evaluation_outputs\evaluation_predictions.csv`
- `evaluation_outputs\evaluation_report.md`

### 3. Run Live Inference / Testing

Run:

```powershell
python rsl_testare_live.py
```

Run with a specific saved model:

```powershell
python rsl_testare_live.py --model saved_models\best_model.h5
python rsl_testare_live.py --model saved_models\rsl_20260215_0300.h5
```

What happens:

- The script loads the trained model.
- It reads class names from `saved_models\sign_classes.txt`.
- It opens the webcam.
- It builds a rolling frame buffer.
- It runs real-time predictions and shows confidence bars on screen.
- It prints live confidence and latency in the console when confidence passes the threshold.

This script is the toolkit's inference/test command.

## Typical Workflow

```powershell
python rsl_data_collector.py
python rsl_model_trainer.py --epochs 300 --augment
python rsl_testare_live.py --model saved_models\best_model.h5
```

## GPU and CPU Execution

`rsl_model_trainer.py` and `rsl_testare_live.py` now do GPU-first startup detection.

At startup they:

- print the TensorFlow version
- print visible GPUs
- prefer GPU automatically if one is available
- try to enable TensorFlow GPU memory growth
- fall back safely to CPU if no GPU is available or GPU initialization fails

Typical GPU startup messages:

```text
[TensorFlow] Version: <tf-version>
[TensorFlow] Visible GPUs: ['<gpu-name>']
[TensorFlow] GPU detected. TensorFlow will use the default visible GPU.
[TensorFlow] Memory growth enabled for visible GPU(s).
[TensorFlow] Execution device: GPU
```

Typical CPU fallback messages:

```text
[TensorFlow] Version: <tf-version>
[TensorFlow] Visible GPUs: []
[TensorFlow] No GPU detected. Falling back to CPU execution.
[TensorFlow] Execution device: CPU
```

## Important Paths

| Path | Meaning |
|---|---|
| `dataset\landmarks` | Recorded landmark sequences used for training |
| `dataset\clips` | Raw recorded videos |
| `saved_models` | Best checkpoint and final saved models |
| `evaluation_outputs` | Metrics, plots, reports, and confusion matrix exports |
| `mp_models` | Downloaded MediaPipe task files |
| `docs\DIAGRAMS.md` | Diagram reference document |

## Troubleshooting

### `No webcam.`

A webcam was not detected or could not be opened by OpenCV.

### `No landmarks folder. Run collector first.`

You tried to train before recording data.
Run:

```powershell
python rsl_data_collector.py
```

### `No classes found.` or `No data loaded.`

The dataset folder exists, but there are no valid `.npy` training sequences inside it.

### `Model not found:`

You tried to run live testing before training, or you passed a wrong model path.
Use one of:

```powershell
python rsl_model_trainer.py
python rsl_testare_live.py --model saved_models\best_model.h5
```

### `No classes file.`

The live tester could not find `saved_models\sign_classes.txt`.
Train the model again so the trainer exports the class metadata.

## Notes

- The toolkit is offline and file-based.
- The collector creates the dataset.
- The trainer produces the model.
- The live tester performs inference/testing.
- Model architecture, dataset format, and training logic are unchanged by the GPU execution update.
