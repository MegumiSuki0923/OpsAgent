"""诊断 Agent 状态定义。"""

from typing import Annotated, TypedDict
from langgraph.graph import add_messages


class DiagnosisState(TypedDict):
    """贯穿整个诊断工作流的共享状态。"""
    user_query: str                                    # 用户原始问题
    parsed_intent: dict                                # 解析后的意图
    anomaly_results: list[dict]                        # 异常检测结果
    knowledge_results: list[dict]                      # RAG 检索结果
    diagnosis_report: str                              # 最终诊断报告
    iteration: int                                     # 当前推理轮次
    messages: Annotated[list, add_messages]             # 对话历史
