"""综合诊断节点：汇总异常检测和知识检索结果，生成诊断报告。"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import DiagnosisState
from ..prompts.templates import DIAGNOSIS_PROMPT


def _get_llm() -> ChatOpenAI:
    provider = os.getenv("LLM_PROVIDER", "deepseek")
    if provider == "deepseek":
        return ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))


async def generate_diagnosis(state: DiagnosisState) -> dict:
    """汇总所有信息，生成结构化诊断报告。"""
    llm = _get_llm()

    context = _build_context(state)

    response = await llm.ainvoke([
        SystemMessage(content=DIAGNOSIS_PROMPT),
        HumanMessage(content=context),
    ])

    return {
        "diagnosis_report": response.content,
        "messages": [response],
    }


def _build_context(state: DiagnosisState) -> str:
    """将状态中的信息组装为 LLM 输入上下文。"""
    parts = []

    parts.append(f"## 用户问题\n{state['user_query']}")

    intent = state.get("parsed_intent", {})
    if intent:
        parts.append(f"## 解析意图\n{json.dumps(intent, ensure_ascii=False, indent=2)}")

    anomalies = state.get("anomaly_results", [])
    if anomalies:
        parts.append(f"## 异常检测结果\n共发现 {len(anomalies)} 个异常段：")
        for i, a in enumerate(anomalies, 1):
            parts.append(
                f"  {i}. 位置 [{a['start_idx']}-{a['end_idx']}], "
                f"类型={a['anomaly_type']}, 置信度={a['confidence']}, "
                f"方法={a.get('method', 'unknown')}"
            )
    else:
        parts.append("## 异常检测结果\n未检测到明显异常。")

    knowledge = state.get("knowledge_results", [])
    if knowledge:
        parts.append(f"## 相关运维知识（共 {len(knowledge)} 条）")
        for i, k in enumerate(knowledge, 1):
            parts.append(f"  [{i}] (来源: {k.get('source', 'unknown')})\n  {k['content'][:500]}")
    else:
        parts.append("## 相关运维知识\n知识库中未找到直接相关的案例。")

    return "\n\n".join(parts)
