"""FastAPI 服务入口。"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 OpsAgent API 启动中...")
    yield
    print("👋 OpsAgent API 关闭")


app = FastAPI(
    title="OpsAgent API",
    description="基于 MCP 的智能运维诊断系统",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagnoseRequest(BaseModel):
    query: str
    metric_data: list[float] | None = None
    timestamps: list[str] | None = None


class DiagnoseResponse(BaseModel):
    query: str
    report: str
    anomaly_count: int
    knowledge_count: int


@app.post("/api/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    """执行端到端诊断。"""
    from agent.graph import workflow

    result = await workflow.ainvoke({
        "user_query": req.query,
        "parsed_intent": {},
        "anomaly_results": [],
        "knowledge_results": [],
        "diagnosis_report": "",
        "iteration": 0,
        "messages": [],
    })

    return DiagnoseResponse(
        query=req.query,
        report=result.get("diagnosis_report", "诊断失败"),
        anomaly_count=len(result.get("anomaly_results", [])),
        knowledge_count=len(result.get("knowledge_results", [])),
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ops-agent"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)
