# Code Audit Agent

AI-powered code security auditor that analyzes any public GitHub repository for vulnerabilities, code quality issues, and best practice violations.

Built with LangChain, Google Gemini, AstraDB, and FastAPI.

## Architecture

```
```

## Project Structure

```
code-audit-agent/
│
├── app.py                      # Entry point — FastAPI setup, run with `python app.py`
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render deployment config
├── .env.example                # Environment variable template
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── config.py               # Centralized settings from env vars
│   │
│   ├── api/                    # HTTP layer
│   │   ├── __init__.py
│   │   ├── routes.py           # All API endpoints (/chat, /load-repo, /auth, /health)
│   │   └── middleware.py       # Rate limiting + session authentication
│   │
│   ├── agent/                  # LLM agent
│   │   ├── __init__.py
│   │   └── builder.py          # Constructs LangChain agent with tools + prompt
│   │
│   ├── tools/                  # Agent tools
│   │   ├── __init__.py
│   │   ├── analyzer.py         # Bandit static analysis + code quality checks
│   │   └── notes.py            # Save/retrieve audit findings
│   │
│   ├── services/               # External service integrations
│   │   ├── __init__.py
│   │   ├── github.py           # GitHub API — issues, PRs, code fetching
│   │   └── vectorstore.py      # AstraDB connection + document loading
│   │
│   └── static/                 # Frontend
│       └── index.html          # Chat UI
│
└── tests/                      # Unit tests
    ├── __init__.py
    ├── test_github.py           # GitHub URL parsing tests
    └── test_tools.py            # Notes tool tests
```

## Features

- **Dynamic Repository Loading** — Analyze any public GitHub repo by URL or `owner/repo`
- **Multi-Source Ingestion** — Fetches issues, pull requests (with diffs), and source code
- **RAG-Powered Search** — Semantic search over repo context via vector embeddings
- **Static Analysis** — Bandit security scanning for Python codebases
- **Code Quality Checks** — Detects hardcoded secrets, long functions, bare excepts, missing error handling
- **Severity Ratings** — CRITICAL / WARNING / INFO classification
- **Authentication** — Optional password protection for deployed instances
- **Rate Limiting** — Per-IP request throttling (configurable)
- **Audit Notes** — Agent saves and retrieves findings during a session
- **Health Endpoint** — `/api/health` for monitoring

## Tech Stack

| Layer             | Technology                        |
| ----------------- | --------------------------------- |
| LLM               | Google Gemini 1.5 Flash           |
| Embeddings        | Google Generative AI Embeddings   |
| Agent Framework   | LangChain                         |
| Vector Database   | DataStax AstraDB                  |
| Static Analysis   | Bandit                            |
| Backend           | FastAPI + Uvicorn                 |
| Data Source        | GitHub REST API                   |
| Deployment        | Render (free tier)                |

## Setup

### Prerequisites

- Python 3.10–3.12 (3.14 is NOT supported)
- [Google AI Studio API key](https://aistudio.google.com/app/apikey)
- [DataStax AstraDB account](https://astra.datastax.com) (free tier)
- [GitHub Personal Access Token](https://github.com/settings/tokens) (optional, higher rate limits)

### Install

```bash
git clone https://github.com/YOUR_USERNAME/code-audit-agent.git
cd code-audit-agent

python3.10 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Fill in your API keys in .env
```

### Run Locally

```bash
python app.py
# Open http://localhost:8000
```

### Run Tests

```bash
pytest tests/ -v
```

or find it in: https://code-audit-agent.onrender.com

## Usage Examples

1. Load a repo: `pallets/flask` or `https://github.com/pallets/flask`
2. Ask the agent:
   - "Run a full security audit"
   - "Find hardcoded secrets or API keys"
   - "Review the authentication implementation"
   - "Check for SQL injection vulnerabilities"
   - "What are the most critical open issues?"
   - "Analyze error handling in the codebase"

## License

MIT
