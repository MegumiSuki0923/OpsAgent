"""异常检测评估脚本：在 NAB 数据集上计算 Precision / Recall / F1。"""

import json
import csv
from pathlib import Path

import numpy as np

from mcp_servers.anomaly_detection.detectors.isolation_forest import IsolationForestDetector
from mcp_servers.anomaly_detection.detectors.statistical import StatisticalDetector


def load_nab_file(csv_path: str) -> tuple[list[float], list[int]]:
    """加载 NAB CSV 文件，返回 (values, labels)。"""
    values, labels = [], []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            values.append(float(row["value"]))
            labels.append(int(row.get("label", 0)))
    return values, labels


def points_to_labels(anomalies: list[dict], n: int) -> np.ndarray:
    """将异常段列表转为逐点标签。"""
    pred = np.zeros(n, dtype=int)
    for a in anomalies:
        pred[a["start_idx"] : a["end_idx"] + 1] = 1
    return pred


def compute_metrics(true: np.ndarray, pred: np.ndarray) -> dict:
    tp = int(np.sum((pred == 1) & (true == 1)))
    fp = int(np.sum((pred == 1) & (true == 0)))
    fn = int(np.sum((pred == 0) & (true == 1)))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "fn": fn,
    }


def evaluate(data_dir: str = "./data/nab_sample"):
    data_path = Path(data_dir)
    csv_files = list(data_path.glob("*.csv"))
    if not csv_files:
        print(f"⚠️  未找到数据文件于 {data_dir}，请先运行 scripts/download_data.py")
        return

    results = {}
    for method_name, detector in [
        ("isolation_forest", IsolationForestDetector(contamination=0.05)),
        ("statistical", StatisticalDetector(z_threshold=2.5)),
    ]:
        all_true, all_pred = [], []
        for csv_file in csv_files:
            values, labels = load_nab_file(str(csv_file))
            anomalies = detector.detect(values)
            pred = points_to_labels(anomalies, len(values))
            all_true.append(np.array(labels))
            all_pred.append(pred)

        true_concat = np.concatenate(all_true)
        pred_concat = np.concatenate(all_pred)
        metrics = compute_metrics(true_concat, pred_concat)
        results[method_name] = metrics
        print(f"\n📊 {method_name}: P={metrics['precision']:.3f}  R={metrics['recall']:.3f}  F1={metrics['f1']:.3f}")

    print("\n" + json.dumps(results, indent=2))


if __name__ == "__main__":
    evaluate()
