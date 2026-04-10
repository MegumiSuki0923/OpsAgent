"""
运维知识 RAG MCP Server
提供 search_ops_knowledge 工具，基于混合检索 + 重排。
"""

import json
from mcp.server.fastmcp import FastMCP

from .retriever import HybridRetriever

mcp = FastMCP("ops-knowledge-rag")

# 全局 retriever（首次调用时初始化）
_retriever: HybridRetriever | None = None


def _get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


@mcp.tool()
async def search_ops_knowledge(
    query: str,
    top_k: int = 5,
    filter_type: str | None = None,
) -> str:
    """
    从运维知识库中检索与 query 相关的故障案例和解决方案。

    Args:
        query: 搜索查询（如"Kubernetes Pod CrashLoopBackOff 如何排查"）
        top_k: 返回的结果数量（默认 5）
        filter_type: 可选过滤条件 - "k8s" / "linux" / "database" / "network" / None

    Returns:
        JSON 字符串，包含检索结果列表，每个结果含 content, source, score
    """
    retriever = _get_retriever()
    results = retriever.search(query, top_k=top_k, filter_type=filter_type)

    return json.dumps({
        "query": query,
        "result_count": len(results),
        "results": results,
    }, ensure_ascii=False)


@mcp.tool()
async def get_knowledge_stats() -> str:
    """获取知识库统计信息：文档数量、分块数量等。"""
    retriever = _get_retriever()
    stats = retriever.get_stats()
    return json.dumps(stats, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
