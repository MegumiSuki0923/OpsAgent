"""基于滑动窗口统计的异常检测器。"""

import numpy as np


class StatisticalDetector:
    def __init__(self, window_size: int = 20, z_threshold: float = 2.5):
        self.window_size = window_size
        self.z_threshold = z_threshold

    def detect(self, values: list[float]) -> list[dict]:
        arr = np.array(values, dtype=np.float64)
        n = len(arr)
        is_anomaly = np.zeros(n, dtype=bool)
        z_scores = np.zeros(n)

        for i in range(self.window_size, n):
            window = arr[i - self.window_size : i]
            mu, sigma = np.mean(window), np.std(window)
            if sigma < 1e-10:
                sigma = 1e-10
            z = abs(arr[i] - mu) / sigma
            z_scores[i] = z
            if z > self.z_threshold:
                is_anomaly[i] = True

        return self._to_segments(is_anomaly, z_scores)

    def _to_segments(self, flags: np.ndarray, z_scores: np.ndarray) -> list[dict]:
        segments = []
        in_anomaly = False
        start = 0

        for i, flag in enumerate(flags):
            if flag and not in_anomaly:
                start = i
                in_anomaly = True
            elif not flag and in_anomaly:
                max_z = float(np.max(z_scores[start:i]))
                segments.append({
                    "start_idx": start,
                    "end_idx": i - 1,
                    "confidence": round(min(max_z / (self.z_threshold * 2), 1.0), 3),
                    "anomaly_type": "drift" if (i - start) > 5 else "spike",
                    "method": "statistical",
                })
                in_anomaly = False

        if in_anomaly:
            max_z = float(np.max(z_scores[start:]))
            segments.append({
                "start_idx": start,
                "end_idx": len(flags) - 1,
                "confidence": round(min(max_z / (self.z_threshold * 2), 1.0), 3),
                "anomaly_type": "drift" if (len(flags) - start) > 5 else "spike",
                "method": "statistical",
            })

        return segments
