"""端到端诊断评估脚本。"""

import asyncio
import json
import time

from agent.graph import workflow


TEST_CASES = [
    {
        "query": "我们的 API Gateway 服务最近1小时响应时间从 50ms 飙升到了 500ms",
        "expected_in_report": ["响应时间", "异常", "建议"],
    },
    {
        "query": "Kubernetes 集群中 Pod 频繁重启，日志显示 OOMKilled",
        "expected_in_report": ["OOM", "内存", "limits"],
    },
    {
        "query": "MySQL 主从复制延迟越来越大，已经超过了 60 秒",
        "expected_in_report": ["复制", "延迟", "主从"],
    },
]


async def run_single(case: dict) -> dict:
    start = time.time()
    try:
        result = await workflow.ainvoke({
            "user_query": case["query"],
            "parsed_intent": {},
            "anomaly_results": [],
            "knowledge_results": [],
            "diagnosis_report": "",
            "iteration": 0,
            "messages": [],
        })
        elapsed = time.time() - start
        report = result.get("diagnosis_report", "")
        hits = sum(
            1 for kw in case["expected_in_report"]
            if kw.lower() in report.lower()
        )
        return {
            "query": case["query"][:50],
            "success": len(report) > 50,
            "keyword_hits": f"{hits}/{len(case['expected_in_report'])}",
            "report_length": len(report),
            "elapsed_s": round(elapsed, 2),
        }
    except Exception as e:
        return {
            "query": case["query"][:50],
            "success": False,
            "error": str(e),
            "elapsed_s": round(time.time() - start, 2),
        }


async def evaluate():
    print("🔬 端到端诊断评估\n")
    results = []
    for case in TEST_CASES:
        r = await run_single(case)
        status = "✅" if r["success"] else "❌"
        print(f"{status} {r['query']}  关键词={r.get('keyword_hits', 'N/A')}  耗时={r['elapsed_s']}s")
        results.append(r)

    success_rate = sum(1 for r in results if r["success"]) / len(results)
    avg_time = sum(r["elapsed_s"] for r in results) / len(results)
    print(f"\n📊 成功率: {success_rate:.0%}  平均耗时: {avg_time:.1f}s")


if __name__ == "__main__":
    asyncio.run(evaluate())
