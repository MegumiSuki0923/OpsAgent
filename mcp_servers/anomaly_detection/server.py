"""
时序异常检测 MCP Server
提供 detect_anomaly 工具，支持 Isolation Forest 和滑动窗口统计两种检测方法。
"""

import json
from mcp.server.fastmcp import FastMCP

from .detectors.isolation_forest import IsolationForestDetector
from .detectors.statistical import StatisticalDetector

mcp = FastMCP("anomaly-detection")


@mcp.tool()
async def detect_anomaly(
    metric_values: list[float],
    timestamps: list[str] | None = None,
    method: str = "ensemble",
    sensitivity: str = "medium",
) -> str:
    """
    检测时序数据中的异常段。

    Args:
        metric_values: 时序指标值列表（如 CPU 使用率、响应时间等）
        timestamps: 对应的时间戳列表（ISO 格式），可选
        method: 检测方法 - "isolation_forest" / "statistical" / "ensemble"（默认）
        sensitivity: 灵敏度 - "low" / "medium"（默认）/ "high"

    Returns:
        JSON 字符串，包含异常区间列表，每个区间包含 start_idx, end_idx,
        confidence, anomaly_type
    """
    if len(metric_values) < 10:
        return json.dumps({"error": "数据点不足，至少需要 10 个数据点", "anomalies": []})

    sensitivity_map = {"low": 0.01, "medium": 0.05, "high": 0.10}
    contamination = sensitivity_map.get(sensitivity, 0.05)

    anomalies = []

    if method in ("isolation_forest", "ensemble"):
        iforest = IsolationForestDetector(contamination=contamination)
        iforest_results = iforest.detect(metric_values)
        anomalies.extend(iforest_results)

    if method in ("statistical", "ensemble"):
        stat = StatisticalDetector(z_threshold=3.0 - contamination * 20)
        stat_results = stat.detect(metric_values)
        anomalies.extend(stat_results)

    if method == "ensemble":
        anomalies = _merge_anomalies(anomalies)

    # 附上时间戳
    if timestamps:
        for a in anomalies:
            a["start_time"] = timestamps[a["start_idx"]] if a["start_idx"] < len(timestamps) else None
            a["end_time"] = timestamps[a["end_idx"]] if a["end_idx"] < len(timestamps) else None

    return json.dumps({
        "total_points": len(metric_values),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }, ensure_ascii=False)


@mcp.tool()
async def list_methods() -> str:
    """列出支持的异常检测方法及其适用场景。"""
    return json.dumps({
        "methods": [
            {
                "name": "isolation_forest",
                "description": "基于 Isolation Forest 的无监督异常检测，适合捕获全局离群点",
                "best_for": "突发性尖峰、离群值",
            },
            {
                "name": "statistical",
                "description": "基于滑动窗口 Z-score 的统计检测，适合趋势突变和漂移",
                "best_for": "缓慢漂移、均值偏移、周期性异常",
            },
            {
                "name": "ensemble",
                "description": "融合以上两种方法，取并集后合并相邻异常段",
                "best_for": "通用场景（默认推荐）",
            },
        ]
    }, ensure_ascii=False)


def _merge_anomalies(anomalies: list[dict], gap: int = 3) -> list[dict]:
    """合并重叠或相邻的异常区间。"""
    if not anomalies:
        return []

    sorted_a = sorted(anomalies, key=lambda x: x["start_idx"])
    merged = [sorted_a[0].copy()]

    for curr in sorted_a[1:]:
        prev = merged[-1]
        if curr["start_idx"] <= prev["end_idx"] + gap:
            prev["end_idx"] = max(prev["end_idx"], curr["end_idx"])
            prev["confidence"] = max(prev["confidence"], curr["confidence"])
            if curr["anomaly_type"] != prev["anomaly_type"]:
                prev["anomaly_type"] = "mixed"
        else:
            merged.append(curr.copy())

    return merged


if __name__ == "__main__":
    mcp.run()
