"""检索质量评估脚本。"""

import json
from pathlib import Path

from mcp_servers.ops_knowledge_rag.retriever import HybridRetriever


# 手工构造的测试查询和期望答案关键词
TEST_QUERIES = [
    {
        "query": "Kubernetes Pod 一直处于 CrashLoopBackOff 状态怎么办",
        "expected_keywords": ["crashloopbackoff", "kubectl", "logs", "restart"],
    },
    {
        "query": "MySQL 连接数耗尽导致服务不可用",
        "expected_keywords": ["max_connections", "连接池", "mysql", "too many connections"],
    },
    {
        "query": "Linux 服务器 CPU 使用率突然飙高",
        "expected_keywords": ["top", "cpu", "进程", "load"],
    },
    {
        "query": "Nginx 502 Bad Gateway 排查",
        "expected_keywords": ["502", "upstream", "nginx", "proxy"],
    },
    {
        "query": "Redis 内存占用过高 OOM",
        "expected_keywords": ["redis", "内存", "maxmemory", "eviction"],
    },
]


def evaluate(top_k: int = 5):
    try:
        retriever = HybridRetriever()
    except Exception as e:
        print(f"⚠️  无法初始化检索器: {e}")
        print("   请先运行 python -m mcp_servers.ops_knowledge_rag.indexer 构建索引")
        return

    stats = retriever.get_stats()
    print(f"📦 知识库: {stats['total_chunks']} 个分块\n")

    if stats["total_chunks"] == 0:
        print("⚠️  知识库为空，请先构建索引")
        return

    total_hit = 0
    total_queries = len(TEST_QUERIES)

    for tq in TEST_QUERIES:
        results = retriever.search(tq["query"], top_k=top_k)
        all_text = " ".join(r["content"].lower() for r in results)
        hits = sum(1 for kw in tq["expected_keywords"] if kw.lower() in all_text)
        hit_rate = hits / len(tq["expected_keywords"])
        total_hit += hit_rate

        status = "✅" if hit_rate >= 0.5 else "❌"
        print(f"{status} Q: {tq['query'][:40]}...  命中率: {hit_rate:.0%} ({hits}/{len(tq['expected_keywords'])})")

    avg = total_hit / total_queries
    print(f"\n📊 平均关键词命中率 (Recall@{top_k}): {avg:.1%}")


if __name__ == "__main__":
    evaluate()
