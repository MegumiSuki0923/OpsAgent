# OpsAgent — 基于 MCP 的智能运维诊断多 Agent 系统

<p align="center">
  <img src="docs/images/architecture.png" alt="OpsAgent Architecture" width="720"/>
</p>

> **OpsAgent** 将时序异常检测、运维知识 RAG 和大模型推理通过 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 串联为统一的诊断工作流，实现 **"描述问题 → 异常定位 → 根因分析 → 修复建议"** 的端到端自动化。

---

## ✨ 亮点

| 能力 | 说明 |
|------|------|
| **时序异常检测 MCP Server** | Isolation Forest + 滑动窗口统计双引擎，在 NAB 数据集上 F1 达 **xx%** |
| **运维知识 RAG MCP Server** | 向量检索 + BM25 混合召回 + Cross-Encoder 重排，召回率 **xx%** |
| **LangGraph 诊断 Agent** | 多步推理状态机：异常检测 → 知识检索 → 综合诊断 → 结构化报告 |
| **MCP 原生架构** | 每个能力模块都是独立 MCP Server，即插即用，可被任何 MCP 客户端调用 |
| **可量化评估** | 内置评估脚本，覆盖异常检测精度、检索召回率、端到端诊断准确率 |

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────┐
│                   用户 / Web UI                       │
│              "服务X最近1小时响应变慢"                    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              LangGraph 诊断 Agent                     │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ 意图理解  │→│ 异常检测  │→│ 知识检索+根因分析  │  │
│  └──────────┘  └────┬─────┘  └────────┬──────────┘  │
│                     │                  │              │
│         ┌───── MCP 调用 ─────┐  ┌── MCP 调用 ──┐    │
│         ▼                    │  ▼               │    │
│  ┌─────────────┐      ┌─────────────────┐      │    │
│  │ 异常检测     │      │ 运维知识 RAG     │      │    │
│  │ MCP Server  │      │ MCP Server      │      │    │
│  └─────────────┘      └─────────────────┘      │    │
│                                                 │    │
│  ┌──────────────────────────────────────────┐   │    │
│  │           综合推理 → 生成诊断报告          │   │    │
│  └──────────────────────────────────────────┘   │    │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python ≥ 3.11
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip
- LLM API Key (DeepSeek / OpenAI / Anthropic 任选一个)

### 安装

```bash
git clone https://github.com/<your-username>/OpsAgent.git
cd OpsAgent

# 使用 uv（推荐）
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 或使用 pip
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key
```

### 运行

```bash
# 1. 启动异常检测 MCP Server
python -m mcp_servers.anomaly_detection.server

# 2. 启动运维知识 RAG MCP Server
python -m mcp_servers.ops_knowledge_rag.server

# 3. 启动诊断 Agent API
python -m api.main

# 4. (可选) 启动 Web UI
cd web && python -m http.server 8080
```

### 一键启动

```bash
python scripts/start_all.py
```

---

## 📁 项目结构

```
OpsAgent/
├── mcp_servers/
│   ├── anomaly_detection/        # 时序异常检测 MCP Server
│   │   ├── server.py             # MCP Server 入口
│   │   ├── detectors/
│   │   │   ├── isolation_forest.py
│   │   │   └── statistical.py    # 滑动窗口统计检测
│   │   └── utils.py
│   │
│   └── ops_knowledge_rag/        # 运维知识 RAG MCP Server
│       ├── server.py             # MCP Server 入口
│       ├── indexer.py            # 文档索引构建
│       ├── retriever.py          # 混合检索 (向量 + BM25)
│       └── reranker.py           # Cross-Encoder 重排
│
├── agent/
│   ├── graph.py                  # LangGraph 诊断工作流定义
│   ├── state.py                  # Agent State 定义
│   ├── nodes/
│   │   ├── intent_parser.py      # 意图理解节点
│   │   ├── anomaly_caller.py     # 调用异常检测 MCP
│   │   ├── knowledge_caller.py   # 调用 RAG MCP
│   │   └── diagnosis.py          # 综合诊断节点
│   └── prompts/
│       └── templates.py          # Prompt 模板
│
├── api/
│   └── main.py                   # FastAPI 服务入口
│
├── web/                          # 前端 (单页 HTML)
│   └── index.html
│
├── data/
│   ├── nab_sample/               # NAB 数据集样本
│   └── ops_docs/                 # 运维文档语料
│
├── eval/
│   ├── eval_anomaly.py           # 异常检测评估
│   ├── eval_retrieval.py         # 检索质量评估
│   └── eval_e2e.py               # 端到端诊断评估
│
├── scripts/
│   ├── start_all.py              # 一键启动
│   ├── build_index.py            # 构建 RAG 索引
│   └── download_data.py          # 下载数据集
│
├── tests/
│   ├── test_anomaly_server.py
│   ├── test_rag_server.py
│   └── test_agent.py
│
├── docs/
│   ├── images/
│   │   └── architecture.png
│   └── DESIGN.md                 # 设计文档
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── pyproject.toml
```

---

## 🔧 核心模块详解

### 1. 时序异常检测 MCP Server

提供 `detect_anomaly` 工具，接收时序指标数据，返回异常时间段。

**双引擎策略：**
- **Isolation Forest**：无监督，适合捕获全局异常点
- **滑动窗口统计**：基于 Z-score / 移动均值偏差，适合趋势突变和漂移检测

**MCP 工具接口：**
```python
@mcp.tool()
async def detect_anomaly(
    metric_values: list[float],
    timestamps: list[str],
    sensitivity: str = "medium"  # low / medium / high
) -> dict:
    """检测时序数据中的异常段，返回异常区间、置信度和异常类型"""
```

### 2. 运维知识 RAG MCP Server

提供 `search_ops_knowledge` 工具，从运维文档库中检索相关故障案例和解决方案。

**检索链路：**
```
Query → [向量检索 (top-20)] + [BM25 关键词检索 (top-20)]
     → 合并去重
     → Cross-Encoder 重排 (top-5)
     → 返回结果
```

**知识源：**
- Kubernetes 官方 Troubleshooting 文档
- 公开的运维故障案例集
- Stack Overflow 高票运维问答

### 3. LangGraph 诊断 Agent

基于状态机的多步推理工作流：

```
START → intent_parser → anomaly_caller → knowledge_caller → diagnosis → END
                              ↑                                   │
                              └──── 信息不足时循环补充检索 ────────┘
```

**State 定义：**
```python
class DiagnosisState(TypedDict):
    user_query: str               # 用户原始描述
    parsed_intent: dict           # 解析后的意图
    anomaly_results: list[dict]   # 异常检测结果
    knowledge_results: list[dict] # RAG 检索结果
    diagnosis_report: str         # 最终诊断报告
    messages: Annotated[list, add_messages]
```

---

## 📊 评估

```bash
# 异常检测评估 (NAB 数据集)
python eval/eval_anomaly.py

# RAG 检索评估
python eval/eval_retrieval.py

# 端到端评估
python eval/eval_e2e.py
```

| 指标 | 数值 |
|------|------|
| 异常检测 F1 (NAB) | xx% |
| 知识检索 Recall@5 | xx% |
| 端到端诊断准确率 | xx% |
| 平均响应时间 | < x s |

---

## 🛣️ Roadmap

- [x] 时序异常检测 MCP Server (Isolation Forest + Statistical)
- [x] 运维知识 RAG MCP Server (混合检索 + 重排)
- [x] LangGraph 诊断 Agent
- [x] FastAPI 服务 + Web UI
- [x] 评估脚本
- [ ] 支持 Prometheus 实时数据接入
- [ ] 支持更多异常检测算法 (Transformer-based)
- [ ] GraphRAG 拓展：运维知识图谱
- [ ] Docker Compose 一键部署

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
