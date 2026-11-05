# AgentBench — AI Agent 评测与可观测平台 · 设计文档

> 状态：待用户审核
> 日期：2026-07-04
> 作者：头脑风暴产出

---

## 1. 项目定位

一个**框架无关的 Agent 评测平台**：管理测试集、运行 Agent、可视化调用链、自动评分、版本对比、回归测试。

帮 Agent 开发者回答核心问题：

- "我的 Agent 改完之后有没有退化？"
- "换一个模型/Prompt/工具，整体质量是提升了还是下降了？"
- "哪条测试用例出了问题，调用链中哪一环出错？"

### 面试叙事

与 AnimePilot 形成递进关系：

| 维度 | AnimePilot | AgentBench |
|------|-----------|------------|
| 角色 | Agent 应用开发者 | Agent 质量保障者 |
| AI 技术 | 单 Agent 编排（自研） | 评测任意 Agent（框架无关） |
| 核心挑战 | RAG 检索质量、推荐可解释性 | 评测方法学、LLM-as-Judge 可靠性、Trace 标准化 |
| 技术栈新增 | — | LangGraph、LLM-as-Judge、评测方法论 |

---

## 2. 功能设计

### 2.1 MVP 范围（v0）

#### 测试集管理

- 创建/编辑/删除测试用例
- 每个测试用例包含：input（用户输入）、expected_behavior（期望行为描述）、scoring_criteria（评分标准）、tags（标签）、difficulty（难度等级 easy/medium/hard）、category（分类）
- 按标签/分类/难度筛选
- 批量导入/导出（JSON 格式）

#### Agent Runner

支持四种适配器接入不同 Agent：

1. **LangGraph Adapter** — 执行 LangGraph 编译后的 workflow，通过 callback 收集 trace
2. **OpenAI Compatible Adapter** — 调用 `/chat/completions` 端点，解析 response 做 trace
3. **HTTP Adapter** — 调用自定义 HTTP 端点，从响应中提取 trace（需约定格式）
4. **Python Function Adapter** — 直接调用 Python 函数，通过装饰器收集 trace

统一接口：`run(test_input: str, agent_config: AgentConfig) -> list[RunStep]`

#### Trace 可视化

展示每次运行的完整步骤链：

- 步骤类型：intent_detection、tool_call、retrieval、llm_generation、response_build
- 每步记录：input/output JSON、latency_ms、token_usage、status（success/error）、error_message
- 时间线视图，错误步骤标红，耗时异常标黄
- 支持展开查看单步详细数据

#### 自动评分

两种评分方式，可组合使用：

- **规则评分（RuleEvaluator）**
  - 关键词匹配：输出中是否包含/不包含指定关键词
  - 正则匹配：输出是否符合指定模式
  - JSON Schema 校验：输出结构是否符合预期 Schema

- **LLM-as-Judge（LLMJudgeEvaluator）**
  - 构造评测 prompt，包含：用户输入、期望行为、Agent 实际输出、评分维度与标准
  - 调用 LLM 返回结构化评分 JSON
  - 四个评分维度：
    - `accuracy`：回答是否准确回答了用户问题
    - `hallucination`：是否存在幻觉（编造事实）
    - `tool_correctness`：是否调用了正确的工具、参数是否合理
    - `expression_quality`：中文表达是否通顺、专业
  - 每个维度 1-5 分，附带 judge_reasoning

#### 基础 UI

- 测试用例列表页：CRUD + 筛选 + 批量操作
- Agent 配置管理页：添加/编辑/测试连接
- 运行详情页：Trace 时间线 + 评分结果
- 评分汇总页：通过率、平均分、按维度分布

### 2.2 后续迭代（v1+，不在 MVP）

| 功能 | 说明 |
|------|------|
| 版本对比 | prompt-v1 + gpt-4.1 vs prompt-v2 + qwen，展示通过率/平均分/延迟/成本变化 |
| 人工复核 | 低分样本进入 review queue，人工标注通过/失败/部分正确 |
| 回归测试 | 一键跑历史测试集，检测退化，生成 diff 报告 |
| MCP Server | 暴露评测接口，支持 CI/CD 集成 |
| 成本追踪 | 记录每次运行的 token 消耗与费用，按 Agent/模型/时间聚合 |

---

## 3. 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| 后端框架 | FastAPI | 与 AnimePilot 保持一致，降低学习成本 |
| ORM | SQLAlchemy 2.x | 异步支持，与 AnimePilot 保持一致 |
| 数据库 | SQLite（MVP）→ PostgreSQL（生产） | MVP 用 SQLite 零配置启动 |
| 数据校验 | Pydantic v2 | 请求/响应模型、配置模型 |
| 前端框架 | Vue 3 + TypeScript | 与 AnimePilot 保持一致 |
| 构建工具 | Vite | — |
| 状态管理 | Pinia | — |
| UI 组件库 | Naive UI | — |
| Agent 编排 | LangGraph | 作为 Runner 的内部编排引擎，也作为被测对象示例 |
| LLM 接入 | OpenAI 兼容 API | 支持切换不同模型（GPT/Qwen/DeepSeek 等） |
| 测试 | Pytest + Vitest + Playwright | 后端/前端/E2E |

---

## 4. 数据模型

### 4.1 核心实体

```python
# 测试用例
class TestCase(Base):
    id: int (PK)
    title: str                          # 用例标题
    input_text: str                     # 用户输入
    expected_behavior: str              # 期望行为描述
    scoring_criteria: str               # 评分标准（自然语言）
    tags: str                           # JSON 数组，如 ["搜索", "多轮"]
    difficulty: str                     # easy / medium / hard
    category: str                       # 分类
    created_at: datetime
    updated_at: datetime

# Agent 配置
class AgentConfig(Base):
    id: int (PK)
    name: str                           # 配置名称，如 "animepilot-v1"
    agent_type: str                     # langgraph / openai_compatible / http / python_fn
    config: str                         # JSON，存储 endpoint、model、headers 等
    description: str
    created_at: datetime
    updated_at: datetime

# 测试运行（一次 TestCase × AgentConfig 的执行）
class TestRun(Base):
    id: int (PK)
    test_case_id: int (FK → TestCase)
    agent_config_id: int (FK → AgentConfig)
    status: str                         # pending / running / success / error
    agent_output: str                   # Agent 最终输出文本
    duration_ms: int                    # 总耗时
    total_tokens: int                   # 总 token 消耗
    cost_estimate: float                # 估算费用（USD）
    error_message: str | None
    created_at: datetime

# 运行步骤（Trace）
class RunStep(Base):
    id: int (PK)
    test_run_id: int (FK → TestRun)
    sequence: int                       # 步骤序号（从 1 开始）
    step_type: str                      # intent_detection / tool_call / retrieval / llm_generation / response_build
    name: str                           # 步骤名称，如 "IntentDetector"
    input_json: str                     # 步骤输入（JSON）
    output_json: str                    # 步骤输出（JSON）
    latency_ms: int                     # 单步耗时
    token_usage_input: int              # 该步骤 input tokens
    token_usage_output: int             # 该步骤 output tokens
    status: str                         # success / error
    error_message: str | None

# 评分结果
class EvaluationResult(Base):
    id: int (PK)
    test_run_id: int (FK → TestRun)
    judge_type: str                     # rule / llm
    overall_score: float                # 总分（1-5）
    accuracy_score: float | None        # 准确性
    hallucination_score: float | None   # 幻觉（高分=无幻觉）
    tool_correctness_score: float | None # 工具调用正确性
    expression_quality_score: float | None # 表达质量
    judge_reasoning: str               # 评分理由
    rule_results: str | None           # JSON，规则评分的每条规则结果
    created_at: datetime

# 人工复核（v1）
class HumanReview(Base):
    id: int (PK)
    evaluation_result_id: int (FK → EvaluationResult)
    reviewer_verdict: str              # pass / fail / partial
    reviewer_comment: str
    reviewed_at: datetime
```

### 4.2 实体关系

```
TestCase 1──N TestRun N──1 AgentConfig
TestRun   1──N RunStep
TestRun   1──N EvaluationResult
EvaluationResult 1──0..1 HumanReview  (v1)
```

---

## 5. 架构设计

### 5.1 后端模块分层

```
backend/
├── agentbench/
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置管理（环境变量/Pydantic Settings）
│   ├── database.py                 # SQLAlchemy 引擎与 session
│   ├── models/                     # ORM 模型
│   │   ├── test_case.py
│   │   ├── agent_config.py
│   │   ├── test_run.py
│   │   ├── run_step.py
│   │   └── evaluation_result.py
│   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── test_case.py
│   │   ├── agent_config.py
│   │   ├── test_run.py
│   │   ├── run_step.py
│   │   └── evaluation.py
│   ├── routers/                   # API 路由（轻薄层）
│   │   ├── test_cases.py
│   │   ├── agent_configs.py
│   │   ├── test_runs.py
│   │   ├── evaluations.py
│   │   └── traces.py
│   ├── services/                   # 业务逻辑层
│   │   ├── test_case_service.py
│   │   ├── agent_config_service.py
│   │   ├── runner_service.py       # 调度测试运行
│   │   └── evaluation_service.py   # 评分逻辑
│   ├── runners/                    # Agent Runner 适配器
│   │   ├── base.py                 # 抽象基类 AgentRunner
│   │   ├── langgraph_adapter.py
│   │   ├── openai_adapter.py
│   │   ├── http_adapter.py
│   │   └── python_fn_adapter.py
│   ├── evaluators/                 # 评分引擎
│   │   ├── base.py                 # 抽象基类 Evaluator
│   │   ├── rule_evaluator.py
│   │   └── llm_judge_evaluator.py
│   └── utils/                      # 工具函数
│       ├── trace_collector.py      # 统一 trace 收集器
│       └── token_counter.py        # token 计数与成本估算
├── tests/                          # 测试
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── alembic/                        # 数据库迁移（v1 迁移 PostgreSQL 时启用）
```

### 5.2 前端页面结构

```
frontend/
├── src/
│   ├── views/
│   │   ├── TestCases.vue           # 测试用例列表
│   │   ├── TestCaseEdit.vue        # 用例编辑（创建/修改）
│   │   ├── AgentConfigs.vue        # Agent 配置列表
│   │   ├── AgentConfigEdit.vue     # 配置编辑
│   │   ├── RunDetail.vue           # 运行详情（Trace 时间线 + 评分）
│   │   └── Dashboard.vue           # 汇总仪表盘
│   ├── components/
│   │   ├── TraceTimeline.vue       # Trace 时间线组件
│   │   ├── StepDetail.vue          # 单步详情展开
│   │   ├── ScoreCard.vue           # 评分卡片
│   │   └── TestCaseTable.vue       # 用例表格
│   ├── stores/
│   │   ├── testCases.ts
│   │   ├── agentConfigs.ts
│   │   └── testRuns.ts
│   └── api/                        # API 调用层
│       ├── testCases.ts
│       ├── agentConfigs.ts
│       ├── testRuns.ts
│       └── evaluations.ts
```

### 5.3 核心流程

```
用户创建 TestCase + AgentConfig
        │
        ▼
用户点击"运行测试"（单个/批量）
        │
        ▼
RunnerService 接收任务
  ├── 1. 创建 TestRun（status=pending）
  ├── 2. 根据 AgentConfig.agent_type 选择对应 Adapter
  ├── 3. Adapter.run(test_input)
  │     └── 每个步骤通过 TraceCollector 记录为 RunStep
  ├── 4. 更新 TestRun（status=success/error, agent_output, duration, tokens）
  ├── 5. 触发 EvaluationService
  │     ├── RuleEvaluator.run()    → 规则评分结果
  │     └── LLMJudgeEvaluator.run() → LLM 评分结果
  └── 6. 保存 EvaluationResult
        │
        ▼
前端展示 RunDetail（Trace + 评分）
```

---

## 6. 关键设计决策

### 6.1 Trace 标准化

不同 Agent 框架的 trace 格式不同（LangGraph callback vs OpenAI API response vs 自定义 HTTP）。`TraceCollector` 作为统一的中间层，将各适配器的原始 trace 映射为平台统一的 `RunStep` 格式。

适配器职责：
- LangGraph Adapter：注册 LangGraph callback handler，在 `on_chain_start`/`on_tool_start`/`on_llm_end` 等回调中收集信息
- OpenAI Adapter：从 response 的 `usage` 字段提取 token，单次调用记为一个 `llm_generation` 步骤
- HTTP Adapter：约定 Agent 在响应 header 或 body 中返回 trace 数组
- Python Fn Adapter：提供 `@trace_step` 装饰器，函数执行时自动记录

### 6.2 LLM-as-Judge 的可靠性

LLM-as-Judge 的已知问题：
- 位置偏差（position bias）
- 长度偏差（偏爱长回答）
- 自我一致性差

应对策略：
- 评测 prompt 中明确给出评分标准和锚定示例（few-shot）
- 要求先输出分析过程再给分（chain-of-thought），减少随意打分
- 评分结果附带 `judge_reasoning`，支持人工复核时验证
- MVP 阶段接受 LLM Judge 的不完美，v1 通过人工复核校准

### 6.3 异步执行模型

MVP 采用**同步执行 + 前端轮询**：
- 点击运行 → API 同步执行 → 返回结果
- 批量运行时，逐个执行并实时更新 TestRun 状态
- 前端通过 SSE 或轮询获取进度

v1 升级为**后台任务队列**（Celery 或 arq）：
- 大批量测试不阻塞 API
- 支持取消正在运行的任务

### 6.4 数据库选型

MVP 用 SQLite：
- 零配置，开箱即用
- 开发阶段足够
- Trace 数据量可控（MVP 阶段预计 < 10k 条 RunStep）

后续迁移 PostgreSQL：
- 并发写入性能更好
- JSON 查询更成熟
- 便于部署到生产环境

迁移路径：SQLAlchemy abstracts 隐藏了大部分差异，切换只需改连接字符串 + 少量 SQLite 特有语法（如 JSON 函数）。

---

## 7. 测试策略

### 7.1 后端测试（Pytest）

| 层级 | 数量目标 | 覆盖内容 |
|------|---------|---------|
| Service | ~30 | RunnerService 调度逻辑、EvaluationService 评分逻辑、降级路径 |
| Runner 适配器 | ~15 | 各适配器的 trace 收集、错误处理、超时控制 |
| Evaluator | ~15 | RuleEvaluator 各规则类型、LLMJudgeEvaluator prompt 构造与结果解析 |
| API | ~15 | 端到端 API 调用，参数校验、权限、错误响应 |
| Model | ~10 | 数据库 CRUD 边界情况 |

### 7.2 前端测试（Vitest + Playwright）

| 层级 | 数量目标 | 覆盖内容 |
|------|---------|---------|
| 组件 | ~15 | TraceTimeline 渲染、ScoreCard 显示、表格交互 |
| E2E | ~5 | 创建用例 → 运行 → 查看结果的完整流程 |

---

## 8. 不做什么（YAGNI）

以下明确排除在 MVP 之外：

- 多用户系统 / 登录注册（MVP 单用户，无需鉴权）
- WebSocket 实时推送（用 SSE 或轮询替代）
- Docker 部署 / CI/CD 配置（先保证功能可用）
- 多数据库支持抽象（先 SQLite，后续再迁移）
- 国际化（中文即可）
- Agent 的并发压测（MVP 串行执行）
- 数据导出为 PDF/Excel（JSON 够用）
