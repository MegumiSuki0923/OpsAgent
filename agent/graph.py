"""LangGraph 诊断工作流定义。"""

from langgraph.graph import StateGraph, END

from .state import DiagnosisState
from .nodes.intent_parser import parse_intent
from .nodes.anomaly_caller import call_anomaly_detection
from .nodes.knowledge_caller import call_knowledge_rag
from .nodes.diagnosis import generate_diagnosis


def should_continue(state: DiagnosisState) -> str:
    """判断是否需要继续补充信息。"""
    if state.get("iteration", 0) >= 2:
        return "diagnose"
    if not state.get("knowledge_results"):
        return "search_knowledge"
    return "diagnose"


def build_graph() -> StateGraph:
    """构建诊断 Agent 工作流图。"""
    graph = StateGraph(DiagnosisState)

    # 添加节点
    graph.add_node("parse_intent", parse_intent)
    graph.add_node("detect_anomaly", call_anomaly_detection)
    graph.add_node("search_knowledge", call_knowledge_rag)
    graph.add_node("diagnose", generate_diagnosis)

    # 定义边
    graph.set_entry_point("parse_intent")
    graph.add_edge("parse_intent", "detect_anomaly")
    graph.add_edge("detect_anomaly", "search_knowledge")
    graph.add_conditional_edges("search_knowledge", should_continue, {
        "search_knowledge": "search_knowledge",
        "diagnose": "diagnose",
    })
    graph.add_edge("diagnose", END)

    return graph.compile()


# 预编译的工作流实例
workflow = build_graph()
