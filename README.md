# RAG-it

**Graph RAG Code Analysis System** — Upload source code, automatically build a dependency graph, and query your codebase architecture with AI-powered insights.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)

## Features

- **Multi-language parsing** — Python, JavaScript, TypeScript, JSX/TSX, Go, Java, and Vue SFC (Single File Components)
- **Interactive dependency graph** — Visualize code structure with a force-directed graph (zoom, pan, click-to-explore)
- **Multi-project support** — Create, switch between, and manage independent projects, each with its own isolated graph
- **AI-powered architecture analysis** — Uses [ZhipuAI GLM-4](https://open.bigmodel.cn/) to identify patterns, analyze dependencies, and suggest improvements
- **Semantic code search** — Find relevant code nodes using [ZhipuAI Embedding-3](https://open.bigmodel.cn/) vector similarity
- **Real-time WebSocket updates** — Watch parsing progress and AI analysis stream in live
- **Spring-themed UI** — Built with Tailwind CSS, featuring a cherry blossom petal animation

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (React 18 + TypeScript + Vite)        │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Sidebar  │  │  ForceGraph  │  │  AI Chat  │  │
│  │ Projects  │  │  (2D Graph)  │  │  Panel    │  │
│  │ Upload    │  │  Controls    │  │  Stream   │  │
│  └──────────┘  └──────────────┘  └───────────┘  │
│       │              │                │          │
│       ▼              ▼                ▼          │
│  Zustand Stores  ◄────  WebSocket ──────►       │
└─────────────────────────┬───────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼───────────────────────┐
│  Backend (FastAPI + SQLite)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Upload   │  │  Parser  │  │  AI Service  │   │
│  │  Router   │  │  Service │  │  (GLM-4)     │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Graph   │  │ Project  │  │  Embedding   │   │
│  │  Router  │  │  Router  │  │  (Embed-3)   │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│  ┌───────────────────────────────────────────┐   │
│  │  SQLite (SQLModel) + NetworkX             │   │
│  └───────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Zustand, react-force-graph-2d |
| **Backend** | FastAPI, Uvicorn, SQLModel, SQLite, NetworkX |
| **Parsers** | Python `ast`, regex-based parsers for JS/TS/Go/Java/Vue |
| **AI** | ZhipuAI GLM-4 (chat), ZhipuAI Embedding-3 (semantic search) |
| **Real-time** | WebSocket with JSON message protocol |
| **DevOps** | Docker Compose, nginx (production) |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) ZhipuAI API key from [open.bigmodel.cn](https://open.bigmodel.cn)

### 1. Clone

```bash
git clone https://github.com/WeiGuang-2099/RAG-tree.git
cd RAG-tree
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Configure API key (optional — AI features disabled without it)
cp .env.example .env
# Edit .env and add your ZHIPUAI_API_KEY
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

### 4. Run

```bash
# Terminal 1 — Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Docker Compose

```bash
ZHIPUAI_API_KEY=your_key_here docker compose up --build
```

## Supported Languages

| Language | Extensions | Parser |
|----------|-----------|--------|
| Python | `.py` | `ast` module |
| JavaScript / TypeScript | `.js`, `.ts`, `.tsx`, `.jsx` | Regex-based |
| Go | `.go` | Regex-based |
| Java | `.java` | Regex-based |
| Vue SFC | `.vue` | Regex-based (Composition API + Options API) |

## Project Structure

```
RAG-it/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + WebSocket endpoint
│   │   ├── config.py            # Settings (Pydantic BaseSettings)
│   │   ├── database.py          # SQLite engine + session
│   │   ├── models/
│   │   │   └── project.py       # Project, File, CodeNode, CodeEdge
│   │   ├── parsers/
│   │   │   ├── base.py          # BaseParser abstract class
│   │   │   ├── python_parser.py
│   │   │   ├── javascript_parser.py
│   │   │   ├── go_parser.py
│   │   │   ├── java_parser.py
│   │   │   └── vue_parser.py
│   │   ├── routers/
│   │   │   ├── upload.py        # File upload → parse → graph pipeline
│   │   │   ├── graph.py         # Graph query endpoints
│   │   │   ├── projects.py      # Project CRUD
│   │   │   └── ai.py            # AI chat, architecture, semantic search
│   │   ├── services/
│   │   │   ├── parser_service.py
│   │   │   ├── graph_service.py
│   │   │   └── ai_service.py    # GLM-4 + Embedding-3 wrapper
│   │   ├── ws/
│   │   │   └── manager.py       # WebSocket connection manager
│   │   └── tests/               # 60 tests (pytest)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── graph/           # ForceGraph, NodeDetail, Controls
│   │   │   ├── hooks/           # useWebSocket, useAiChat, useGraphData
│   │   │   ├── layout/          # Header, Sidebar, MainContent
│   │   │   ├── ui/              # FileUpload, ProjectSelector, GlassCard
│   │   │   └── ai/              # AiChatPanel, MessageBubble
│   │   ├── store/               # Zustand stores (graph, chat, project)
│   │   ├── types/
│   │   └── utils/               # API client, WebSocket URL builder
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── .gitignore
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/upload/` | Upload files (creates or adds to project) |
| `GET` | `/api/projects/` | List all projects |
| `POST` | `/api/projects/` | Create a new project |
| `GET` | `/api/projects/{id}` | Get project details |
| `PUT` | `/api/projects/{id}` | Rename project |
| `DELETE` | `/api/projects/{id}` | Delete project |
| `GET` | `/api/graph/full/{id}` | Full graph (nodes + edges) |
| `GET` | `/api/graph/nodes/{id}` | Nodes for a project |
| `GET` | `/api/graph/edges/{id}` | Edges for a project |
| `GET` | `/api/graph/neighbors/{id}/{node}` | Neighbor exploration |
| `POST` | `/api/ai/chat` | Chat with AI about codebase |
| `POST` | `/api/ai/architecture` | AI architecture analysis |
| `POST` | `/api/ai/search` | Semantic search (Embedding-3) |
| `GET` | `/api/ai/status` | AI availability check |
| `WS` | `/ws/{client_id}` | Real-time WebSocket channel |

## Configuration

| Variable | File | Description |
|----------|------|-------------|
| `ZHIPUAI_API_KEY` | `backend/.env` | ZhipuAI API key (optional) |
| `database_url` | `backend/.env` | SQLite connection string (default: `sqlite:///./data/code_analysis.db`) |
| `max_files` | `backend/app/config.py` | Max files per upload (default: 500) |
| `max_file_size_mb` | `backend/app/config.py` | Max file size in MB (default: 5) |

## Running Tests

```bash
cd backend
pytest app/tests/ -v
```

## License

MIT
