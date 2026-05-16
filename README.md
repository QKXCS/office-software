# 智能办公Agent (Smart Office Agent)

面向个人用户和小团队的全模态AI办公助手，零外部依赖即可运行。

## 核心能力

- **智能对话** — 自然语言交互，理解复杂的办公任务指令
- **文档处理** — 上传文档即可问答、摘要、翻译、对比

## 快速开始（零 Docker）

### 环境要求

- Python 3.12+
- Node.js 20+

就这些。数据库用 SQLite（文件存储），向量库用 Qdrant 本地模式，无需安装任何外部服务。

### 1. 配置

```bash
cd D:/ai/bangong
cp .env.example .env
# 编辑 .env 填入 API Key
```

最少只需要一个能用的 LLM API Key：

```env
# 豆包（默认）
DEFAULT_LLM_PROVIDER=doubao
DOUBAO_API_KEY=sk-ark-你的key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DEFAULT_LLM_MODEL=doubao-seed-2-0-lite

# 或者 Claude
# DEFAULT_LLM_PROVIDER=claude
# ANTHROPIC_API_KEY=sk-ant-你的key
```

### 2. 启动后端

```bash
cd backend
py -m venv venv
venv\Scripts\activate
py -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API 文档：http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

打开 http://localhost:3000 开始使用。

## 系统架构

```
┌──────────────────────────────────────────────────┐
│              User Interface (Next.js)             │
│   Web Chat  │  Voice UI  │  Dashboard  │  Docs   │
└──────────────────────┬───────────────────────────┘
                       │  FastAPI
┌──────────────────────┴───────────────────────────┐
│            Agent Core (LangGraph)                 │
│   Orchestrator  │  Planner  │  Executor  │  Mem  │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────┐
│   RAG (Qdrant本地) │ Tools (MCP) │ Multimodal   │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────┴───────────────────────────┐
│         SQLite  │  Qdrant文件  │  内存缓存       │
└──────────────────────────────────────────────────┘
```

## 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| Agent框架 | LangGraph | DAG流程、checkpoint |
| 后端 | Python / FastAPI | 异步原生、Pydantic v2 |
| 前端 | Next.js / React / Tailwind | App Router |
| LLM | 豆包 / Claude / OpenAI | 默认豆包 |
| 向量库 | Qdrant (本地文件模式) | 零部署 |
| 数据库 | SQLite | 零部署 |

## 项目结构

```
bangong/
├── backend/
│   ├── app/
│   │   ├── api/chat.py        # 对话接口 (SSE)
│   │   ├── api/knowledge.py   # 知识库管理
│   │   ├── core/agent/        # Agent核心 (LangGraph)
│   │   ├── core/rag/          # RAG引擎
│   │   ├── core/memory/       # 记忆系统
│   │   ├── core/multimodal/   # 多模态网关
│   │   └── config.py
│   └── requirements.txt
├── frontend/src/app/          # Next.js
├── docker-compose.yml         # 可选：用Docker跑外部服务
└── .env.example
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/api/chat/send` | 发送消息 |
| POST | `/api/chat/stream` | 流式对话 (SSE) |
| POST | `/api/knowledge/ingest/text` | 文本入库 |
| POST | `/api/knowledge/ingest/file` | 文件上传入库 |

## 可选：使用 Docker 跑数据库

如果以后想切换到 PostgreSQL + Qdrant Server + Redis：

```bash
docker compose up -d
# 然后修改 .env 中的 DATABASE_URL 和 QDRANT_URL
```
