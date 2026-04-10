"""Isolation Forest 异常检测器。"""

import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    def __init__(self, contamination: float = 0.05, window_features: bool = True):
        self.contamination = contamination
        self.window_features = window_features

    def detect(self, values: list[float]) -> list[dict]:
        arr = np.array(values, dtype=np.float64)

        if self.window_features:
            features = self._extract_features(arr)
        else:
            features = arr.reshape(-1, 1)

        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=200,
        )
        labels = model.fit_predict(features)
        scores = model.decision_function(features)

        return self._labels_to_segments(labels, scores)

    def _extract_features(self, arr: np.ndarray, window: int = 5) -> np.ndarray:
        """提取滑动窗口特征：原始值、均值、标准差、变化率。"""
        n = len(arr)
        feats = np.zeros((n, 4))
        feats[:, 0] = arr

        for i in range(n):
            start = max(0, i - window)
            w = arr[start : i + 1]
            feats[i, 1] = np.mean(w)
            feats[i, 2] = np.std(w) if len(w) > 1 else 0
            feats[i, 3] = arr[i] - arr[i - 1] if i > 0 else 0

        return feats

    def _labels_to_segments(self, labels: np.ndarray, scores: np.ndarray) -> list[dict]:
        """将逐点标签转换为异常段。"""
        segments = []
        in_anomaly = False
        start = 0

        for i, label in enumerate(labels):
            if label == -1 and not in_anomaly:
                start = i
                in_anomaly = True
            elif label != -1 and in_anomaly:
                seg_scores = scores[start:i]
                segments.append({
                    "start_idx": start,
                    "end_idx": i - 1,
                    "confidence": round(float(1 - np.mean(np.abs(seg_scores))), 3),
                    "anomaly_type": "spike",
                    "method": "isolation_forest",
                })
                in_anomaly = False

        if in_anomaly:
            seg_scores = scores[start:]
            segments.append({
                "start_idx": start,
                "end_idx": len(labels) - 1,
                "confidence": round(float(1 - np.mean(np.abs(seg_scores))), 3),
                "anomaly_type": "spike",
                "method": "isolation_forest",
            })

        return segments
