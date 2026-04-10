# OpsAgent 设计文档

## 1. 设计动机

现有的 RAG 项目大多是通用文档问答系统，缺乏垂直场景的深度。OpsAgent 将 RAG 技术与 AIOps 场景结合，并引入时序异常检测能力，通过 MCP 协议实现模块化架构。

## 2. 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| Agent 编排 | LangGraph | 支持循环、条件分支、状态持久化 |
| 模块通信 | MCP (Model Context Protocol) | 2026 年 AI 工具调用的事实标准 |
| 向量存储 | Chroma | 轻量、嵌入式、适合原型开发 |
| 关键词检索 | BM25 (rank-bm25) | 弥补向量检索在精确匹配上的不足 |
| 重排 | Cross-Encoder (ms-marco-MiniLM) | 提升检索精度 |
| 异常检测 | Isolation Forest + 滑动窗口 Z-score | 互补：前者擅长全局离群，后者擅长趋势突变 |
| API 框架 | FastAPI | 异步、自动文档、Python 生态 |
| LLM | DeepSeek / OpenAI | DeepSeek 性价比高，适合开发阶段 |

## 3. 数据流

```
用户输入 → Intent Parser (LLM) → 结构化意图
    ↓
时序数据源 → Anomaly Detection MCP → 异常段列表
    ↓
异常描述 + 用户问题 → RAG MCP → 相关知识 Top-K
    ↓
全部上下文 → Diagnosis Node (LLM) → 结构化报告
```

## 4. 检索策略

采用混合检索 + 重排的三阶段管线：

1. **粗召回**：向量检索（Chroma）和 BM25 并行执行，各取 Top-20
2. **合并去重**：按内容前 200 字符去重
3. **精排**：Cross-Encoder 对 query-doc pairs 打分，取 Top-5

这种设计兼顾了语义理解（向量）和精确匹配（BM25），在运维场景中尤为重要——运维文档中包含大量专有名词（如 CrashLoopBackOff、502）需要精确匹配。

## 5. 异常检测策略

双引擎 ensemble：
- **Isolation Forest**：对特征空间做随机切分，异常点更容易被隔离。提取滑动窗口特征（均值、标准差、变化率）增强检测能力。
- **滑动窗口统计**：计算每个点相对于前 N 个点的 Z-score，超过阈值判定为异常。适合捕获均值偏移和缓慢漂移。

两种方法结果取并集，合并相邻异常段。

## 6. 评估方案

| 维度 | 方法 | 指标 |
|------|------|------|
| 异常检测 | NAB 数据集 | Precision, Recall, F1 |
| 检索质量 | 手工 query + 关键词命中 | Keyword Hit Rate@K |
| 端到端 | 预定义 case + 关键词匹配 | 成功率, 关键词命中, 延迟 |

## 7. 后续扩展方向

- **Prometheus 接入**：通过 PromQL MCP Server 拉取实时指标
- **GraphRAG**：构建运维知识图谱，支持多跳推理（如"服务 A 依赖服务 B，B 的数据库异常可能影响 A"）
- **Transformer 异常检测**：引入基于 Transformer 的时序异常检测模型，利用预训练权重
- **Docker Compose 部署**：一键容器化部署
