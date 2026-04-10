"""意图理解节点：解析用户问题，提取关键信息。"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import DiagnosisState
from ..prompts.templates import INTENT_PARSE_PROMPT


def _get_llm() -> ChatOpenAI:
    provider = os.getenv("LLM_PROVIDER", "deepseek")
    if provider == "deepseek":
        return ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))


async def parse_intent(state: DiagnosisState) -> dict:
    """从用户描述中提取：服务名、指标类型、时间范围、问题描述。"""
    llm = _get_llm()
    response = await llm.ainvoke([
        SystemMessage(content=INTENT_PARSE_PROMPT),
        HumanMessage(content=state["user_query"]),
    ])

    # LLM 返回 JSON 格式的意图
    import json
    try:
        parsed = json.loads(response.content)
    except json.JSONDecodeError:
        parsed = {
            "service": "unknown",
            "metric_type": "response_time",
            "time_range": "1h",
            "description": state["user_query"],
        }

    return {
        "parsed_intent": parsed,
        "messages": [response],
    }
