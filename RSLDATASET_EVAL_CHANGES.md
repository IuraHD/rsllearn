# RSL Dataset: Offline Evaluation Toolkit Enhancements

This report summarizes the changes made to the offline toolkit to support dissertation-ready evaluation outputs for Chapter 5.

## 📁 Files Changed
1. `rsl_model_trainer.py`
   - Added automated export of metrics and plots.
   - Integrated `pandas` for CSV generation.
   - Integrated `matplotlib` for figure generation.
2. `rsl_testare_live.py`
   - Added real-time inference latency measurement.
   - Added stable prediction logging to console for behavior analysis.

## 🚀 Enhancements Added

### 1. Automated Evaluation Folder
The toolkit now creates an `evaluation_outputs/` directory inside `RSLdataset` every time a training session completes. This ensures that session results are persistent and structured.

### 2. Dissertation-Ready Exports
The following outputs are now generated automatically after model evaluation:
- `metrics_summary.json`: High-level summary of model performance (Accuracy, Macro F1, Weighted Metrics, Input Dimensions).
- `classification_report.csv`: Detailed per-class precision, recall, and f1-score.
- `confusion_matrix.csv`: Raw values for creating custom tables.
- `confusion_matrix.png`: A high-quality heatmap visualization of the model's errors and successes.
- `training_history.png`: Loss and Accuracy curves to demonstrate convergence and avoid overfitting.
- `class_distribution.csv`: Verification of dataset balance.
- `evaluation_predictions.csv`: Raw prediction log for granular error analysis.
- `evaluation_report.md`: A structured summary report for quick inclusion in dissertation drafts.

### 3. Live Evaluation Logging
The `rsl_testare_live.py` script now prints a `[LIVE EVAL]` log whenever a sign is recognized with high confidence. It includes the measured **inference latency in milliseconds**, which is a key technical metric for HCI performance.

## 📊 Output Files Generated
Location: `RSLdataset/evaluation_outputs/`
- [x] `metrics_summary.json`
- [x] `classification_report.csv`
- [x] `confusion_matrix.csv`
- [x] `confusion_matrix.png`
- [x] `training_history.png`
- [x] `class_distribution.csv`
- [x] `evaluation_predictions.csv`
- [x] `evaluation_report.md`

## 🛠️ Usage Instructions
To generate these outputs with your current dataset, simply run the trainer:

```bash
cd RSLdataset
# Recommended for final evaluation
python rsl_model_trainer.py --augment --epochs 200
```

The files will appear in the `evaluation_outputs/` folder upon completion.

## 📝 Assumptions & Notes
- **Split Ratio:** The system follows a **70% / 15% / 15%** split (Train/Validation/Test) to ensure the test metrics are derived from data completely unseen during training or parameter tuning.
- **Library Dependencies:** The scripts assume `matplotlib` and `pandas` are installed in the Python environment.
- **Existing Logic:** All core methodology, landmark feature shapes, and model architectures remain untouched to preserve the mathematical integrity of the original project.
