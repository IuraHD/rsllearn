# GPU Execution Update

## 1. Files changed

- `rsl_model_trainer.py`
- `rsl_testare_live.py`
- `utils.py`
- `docs/GPU_EXECUTION_UPDATE.md`

## 2. What was added

- A shared TensorFlow runtime helper that:
  - prints the TensorFlow version
  - lists visible GPUs
  - enables GPU memory growth when GPUs are available
  - reports whether execution will run on GPU or CPU
  - falls back cleanly to CPU on GPU detection or initialization issues
- Trainer startup logging for the selected execution device
- Live tester startup logging for the selected execution device
- Additional device metadata in `evaluation_outputs/metrics_summary.json`:
  - `device_used`
  - `tensorflow_version`
  - `visible_gpus`
  - `memory_growth_enabled`

## 3. How GPU detection works

- `configure_tensorflow_runtime()` in `utils.py` imports TensorFlow and prints `tf.__version__`.
- It queries `tf.config.list_physical_devices("GPU")`.
- If one or more GPUs are visible, TensorFlow keeps the default visible GPU selection and reports `Execution device: GPU`.
- No explicit multi-GPU strategy was added. If multiple GPUs are visible, TensorFlow uses its default placement behavior.

## 4. How CPU fallback works

- If no GPUs are visible, the helper prints that CPU fallback is being used and reports `Execution device: CPU`.
- If querying or initializing GPUs raises an exception, the helper prints a warning and falls back to CPU instead of crashing.
- The trainer and live tester both exit cleanly if TensorFlow itself is unavailable, rather than failing later with a secondary import error.

## 5. Whether memory growth was enabled

- Yes, the helper attempts to enable memory growth on each visible GPU with `tf.config.experimental.set_memory_growth(...)`.
- If that succeeds for all visible GPUs, the scripts print that memory growth was enabled.
- If memory growth cannot be enabled, the scripts print a warning and continue with TensorFlow's default behavior instead of failing.

## 6. Assumptions or limitations

- Training and inference remain on TensorFlow's normal automatic device placement; no model architecture, dataset format, or training logic was changed.
- No explicit device scope was added because automatic placement is sufficient here and keeps the change minimal.
- CPU fallback is guaranteed for no-GPU systems and for handled GPU initialization failures, but overall execution still requires TensorFlow to be installed.
