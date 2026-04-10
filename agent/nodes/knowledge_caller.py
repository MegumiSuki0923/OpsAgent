"""调用运维知识 RAG MCP Server 的节点。"""

from ..state import DiagnosisState


async def call_knowledge_rag(state: DiagnosisState) -> dict:
    """根据异常检测结果和用户意图，检索相关运维知识。"""
    intent = state.get("parsed_intent", {})
    anomalies = state.get("anomaly_results", [])

    # 构造检索 query：结合用户描述 + 异常特征
    anomaly_types = list({a.get("anomaly_type", "unknown") for a in anomalies})
    query_parts = [intent.get("description", state["user_query"])]
    if anomaly_types:
        query_parts.append(f"异常类型: {', '.join(anomaly_types)}")

    query = " ".join(query_parts)

    # 开发阶段：直接调用 retriever；生产环境通过 MCP 协议调用
    try:
        from mcp_servers.ops_knowledge_rag.retriever import HybridRetriever
        retriever = HybridRetriever()
        results = retriever.search(query, top_k=5)
    except Exception:
        # 知识库尚未构建时，返回空结果
        results = []

    return {
        "knowledge_results": results,
        "iteration": state.get("iteration", 0) + 1,
    }
