# RAG-it

**Graph RAG Code Analysis System** -- Upload source code, automatically build a dependency graph, and query your codebase architecture with AI-powered insights powered by graph topology.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)

## Features

### Core
- **Multi-language parsing** -- Python, JavaScript, TypeScript, JSX/TSX, and Vue SFC (Single File Components)
- **Interactive dependency graph** -- Force-directed visualization with zoom, pan, click-to-explore
- **Multi-project support** -- Create, switch between, and manage independent projects
- **Real-time WebSocket updates** -- Watch parsing progress and AI analysis stream in live

### Graph Intelligence
- **Graph-RAG retrieval pipeline** -- Three-stage pipeline: semantic search finds seed nodes, graph expansion gathers topology context, structured injection into the LLM prompt
- **Cycle detection** -- Detect circular dependencies in your codebase with one click, highlighted in red on the graph
- **Path finding** -- Find shortest dependency paths between any two code nodes
- **Graph statistics** -- Node/edge counts, density, DAG check

### AI Features
- **Streaming AI chat** -- SSE-based streaming responses with real-time token display
- **Architecture analysis** -- AI-generated overview of your project structure
- **Semantic code search** -- Find relevant code using embedding vector similarity (ZhipuAI Embedding-3)
- **Referenced node navigation** -- Click AI-referenced code nodes to jump directly to them in the graph

### Dashboard & Visualization
- **Project dashboard** -- Metric cards, language distribution bars, top-10 hub nodes by centrality
- **Code preview panel** -- Syntax-highlighted source code with line numbers and line-range highlighting
- **Graph controls** -- Level filtering (Module/Class/Function), text search, file path filter, cycle toggle
- **Keyboard shortcuts** -- Ctrl+K (search), Ctrl+1-4 (levels), Ctrl+Shift+A (AI panel), F (fit), Escape, ? (help)

### Engineering
- **Error boundaries** -- Graceful error recovery for graph and global UI
- **Singleton services** -- AiService and GraphService injected via FastAPI DI for efficient caching
- **File deletion** -- Delete individual files from a project with cascading cleanup
- **75 backend tests** -- Full pytest suite covering services, routers, parsers, and WebSocket

## Architecture

```
+---------------------------------------------------+
|  Frontend (React 18 + TypeScript + Vite)          |
|  +----------+  +--------------+  +-----------+    |
|  |  Sidebar |  |  MainContent |  |  AI Chat  |    |
|  | Projects |  |  Dashboard   |  |  Panel    |    |
|  | Upload   |  |  ForceGraph  |  |  Stream   |    |
|  +----------+  |  DetailPanel |  +-----------+    |
|       |        +--------------+        |          |
|       v               v                v          |
|  Zustand Stores  <---  WebSocket ------>          |
+------------------------+--------------------------+
                         | HTTP / WebSocket / SSE
+------------------------v--------------------------+
|  Backend (FastAPI + SQLite)                        |
|  +----------+  +----------+  +----------------+    |
|  |  Upload  |  |  Parser  |  |  AI Service    |    |
|  |  Router  |  |  Service |  |  (GLM-4)       |    |
|  +----------+  +----------+  |  chat_stream() |    |
|  +----------+  +----------+  +----------------+    |
|  |  Graph   |  | Project  |  +----------------+    |
|  |  Router  |  |  Router  |  |  Embedding     |    |
|  |  cycles  |  | dashboard|  |  (Embed-3)     |    |
|  |  path    |  |  files   |  +----------------+    |
|  |  stats   |  +----------+                        |
|  +----------+                                      |
|  +----------------------------------------------+  |
|  |  NetworkX GraphService (subgraph, cycles)    |  |
|  +----------------------------------------------+  |
|  +----------------------------------------------+  |
|  |  SQLite (SQLModel)                           |  |
|  +----------------------------------------------+  |
+----------------------------------------------------+
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Zustand, react-force-graph-2d, react-syntax-highlighter |
| **Backend** | FastAPI, Uvicorn, SQLModel, SQLite, NetworkX |
| **Parsers** | Python `ast`, regex-based parsers for JS/TS/Vue |
| **AI** | ZhipuAI GLM-4 (chat + streaming), ZhipuAI Embedding-3 (semantic search) |
| **Real-time** | WebSocket (progress/graph/streaming), SSE (chat stream) |
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

# Configure API key (optional -- AI features disabled without it)
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
# Terminal 1 -- Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 -- Frontend
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### Docker Compose

```bash
ZHIPUAI_API_KEY=your_key_here docker compose up --build
```

## Supported Languages

| Language | Extensions | Parser |
|----------|-----------|--------|
| Python | `.py` | `ast` module |
| JavaScript / TypeScript | `.js`, `.ts`, `.tsx`, `.jsx` | Regex-based |
| Vue SFC | `.vue` | Regex-based (Composition API + Options API) |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Focus search input |
| `Ctrl+1` | Show all node types |
| `Ctrl+2` | Show modules only |
| `Ctrl+3` | Show classes only |
| `Ctrl+4` | Show functions only |
| `Ctrl+Shift+A` | Toggle AI chat panel |
| `F` | Fit graph to viewport |
| `Escape` | Deselect node / close panel |
| `?` | Show shortcuts help |

## API Endpoints

### General

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `WS` | `/ws/{client_id}` | Real-time WebSocket channel |

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/projects/` | List all projects |
| `POST` | `/api/projects/` | Create a new project |
| `GET` | `/api/projects/{id}` | Get project details |
| `PUT` | `/api/projects/{id}` | Rename project |
| `DELETE` | `/api/projects/{id}` | Delete project and all data |
| `DELETE` | `/api/projects/{id}/files/{file_id}` | Delete a single file |
| `GET` | `/api/projects/{id}/dashboard` | Project metrics dashboard |

### Graph

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/graph/full/{id}` | Full graph (nodes + edges) |
| `GET` | `/api/graph/nodes/{id}` | Nodes for a project |
| `GET` | `/api/graph/edges/{id}` | Edges for a project |
| `GET` | `/api/graph/neighbors/{id}/{node}` | Neighbor exploration (`?depth=1-3`) |
| `GET` | `/api/graph/path/{id}?from=X&to=Y` | Shortest path between two nodes |
| `GET` | `/api/graph/stats/{id}` | Graph statistics |
| `GET` | `/api/graph/cycles/{id}` | Cycle detection results |

### AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ai/status` | AI availability check |
| `POST` | `/api/ai/chat` | Chat with AI (full response) |
| `POST` | `/api/ai/chat/stream` | Chat with AI (SSE streaming) |
| `POST` | `/api/ai/architecture` | AI architecture analysis |
| `POST` | `/api/ai/search` | Semantic search (Embedding-3) |

### Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload/` | Upload files (creates or adds to project) |

## Configuration

| Variable | File | Description |
|----------|------|-------------|
| `ZHIPUAI_API_KEY` | `backend/.env` | ZhipuAI API key (optional) |
| `database_url` | `backend/.env` | SQLite connection string |
| `max_files` | `backend/app/config.py` | Max files per upload (default: 500) |
| `max_file_size_mb` | `backend/app/config.py` | Max file size in MB (default: 5) |
| `allowed_origins` | `backend/app/config.py` | CORS allowed origins |
| `embedding_cache_enabled` | `backend/app/config.py` | Enable embedding cache (default: true) |

## Project Structure

```
RAG-it/
+-- backend/
|   +-- app/
|   |   +-- main.py                # FastAPI app + WebSocket + CORS
|   |   +-- config.py              # Settings (Pydantic BaseSettings)
|   |   +-- database.py            # SQLite engine + session + service singletons
|   |   +-- models/
|   |   |   +-- project.py         # Project, File, CodeNode, CodeEdge
|   |   +-- parsers/
|   |   |   +-- base.py            # BaseParser abstract class
|   |   |   +-- python_parser.py   # Python AST parser
|   |   |   +-- javascript_parser.py  # JS/TS parser
|   |   |   +-- vue_parser.py      # Vue SFC parser
|   |   +-- routers/
|   |   |   +-- upload.py          # File upload + parse + graph pipeline
|   |   |   +-- graph.py           # Graph query, path, stats, cycles
|   |   |   +-- projects.py        # Project CRUD + dashboard + file delete
|   |   |   +-- ai.py              # AI chat, streaming, architecture, search
|   |   +-- services/
|   |   |   +-- parser_service.py  # Parser dispatch + registry
|   |   |   +-- graph_service.py   # NetworkX graph (subgraph, cycles, path)
|   |   |   +-- ai_service.py      # GLM-4 + Embedding-3 + graph serialization
|   |   +-- ws/
|   |   |   +-- manager.py         # WebSocket connection manager
|   |   +-- tests/                 # 75 tests (pytest)
|   +-- requirements.txt
|   +-- Dockerfile
+-- frontend/
|   +-- src/
|   |   +-- App.tsx                # Root with ErrorBoundary + shortcuts
|   |   +-- components/
|   |   |   +-- graph/             # ForceGraph, NodeDetailPanel, GraphControls
|   |   |   +-- dashboard/        # ProjectDashboard (metrics + hubs)
|   |   |   +-- hooks/            # useWebSocket, useAiChat, useGraphData, useKeyboardShortcuts
|   |   |   +-- layout/           # Header, Sidebar, MainContent
|   |   |   +-- ui/               # FileUpload, ProjectSelector, GlassCard, ErrorBoundary, ShortcutsHelpModal
|   |   |   +-- ai/               # AiChatPanel, MessageBubble, ArchitectureButton
|   |   +-- store/                # Zustand stores (graph, chat, project)
|   |   +-- types/                # TypeScript interfaces
|   |   +-- utils/                # API client, WebSocket URL builder
|   +-- package.json
|   +-- Dockerfile
+-- docker-compose.yml
+-- .gitignore
```

## Running Tests

```bash
cd backend
pytest app/tests/ -v
```

## License

MIT
