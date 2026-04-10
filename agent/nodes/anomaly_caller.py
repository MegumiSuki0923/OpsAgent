"""调用异常检测 MCP Server 的节点。"""

import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..state import DiagnosisState


async def call_anomaly_detection(state: DiagnosisState) -> dict:
    """
    调用异常检测 MCP Server。
    在实际部署中通过 MCP 协议调用；开发时可直接调用检测函数。
    """
    intent = state.get("parsed_intent", {})

    # TODO: 在生产环境中，这里从 Prometheus/时序数据库拉取真实数据
    # 开发阶段使用模拟数据或 NAB 数据集样本
    from mcp_servers.anomaly_detection.detectors.isolation_forest import IsolationForestDetector
    from mcp_servers.anomaly_detection.detectors.statistical import StatisticalDetector
    import numpy as np

    # 模拟数据（开发阶段，后续替换为真实数据源）
    np.random.seed(42)
    normal = np.random.normal(50, 5, 100).tolist()
    # 注入异常
    normal[70:80] = [120 + np.random.normal(0, 3) for _ in range(10)]
    metric_values = normal

    # 双引擎检测
    iforest = IsolationForestDetector(contamination=0.05)
    stat = StatisticalDetector(z_threshold=2.5)

    anomalies = iforest.detect(metric_values) + stat.detect(metric_values)

    return {
        "anomaly_results": anomalies,
        "iteration": state.get("iteration", 0),
    }
