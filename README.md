# GitHub Repository Summarizer API

A FastAPI service that analyzes GitHub repositories and generates intelligent summaries using Large Language Models (LLMs).

## Features

- ✅ Analyzes public GitHub repositories
- ✅ Web UI at `http://localhost:8000` — no curl needed
- ✅ Detailed summaries: overview, technologies, architecture, key features, use cases, and getting started guide
- ✅ Intelligent file filtering and prioritization
- ✅ Context-aware LLM prompting
- ✅ Support for multiple LLM providers (Nebius, Anthropic, OpenAI)
- ✅ GitHub token support to avoid API rate limits
- ✅ Comprehensive error handling
- ✅ RESTful API with proper HTTP status codes

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Git (optional, for cloning)

### Installation

1. **Download and extract the project** (or clone if using git):
```bash
# If cloning:
git clone <your-repo-url>
cd github-summarizer

# If from zip:
unzip github-summarizer.zip
cd github-summarizer
```

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure API keys**:

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Then edit `.env` and add your keys:

```bash
# LLM API key (required) — pick one:
NEBIUS_API_KEY=your-actual-nebius-api-key-here
# ANTHROPIC_API_KEY=your-actual-anthropic-api-key-here
# OPENAI_API_KEY=your-actual-openai-api-key-here

# GitHub token (recommended) — avoids GitHub API rate limits
# Generate at: https://github.com/settings/tokens
GITHUB_TOKEN=your-github-token-here
```

> **Note**: Without a `GITHUB_TOKEN` you are limited to 60 GitHub API requests per hour. With a token the limit rises to 5,000.

> **Note**: The `.env` file is automatically ignored by git (see `.gitignore`) to keep your keys secure.

### Running the Server

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server starts at `http://localhost:8000`. You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press `Ctrl+C` to stop it.

## Usage

### Web UI (recommended)

Open your browser and go to:
```
http://localhost:8000
```

Paste any public GitHub URL into the input box and click **Summarize**. Results appear on the page.

### API (curl)

**Endpoint**: `POST /summarize`

```bash
curl -s -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}' | python3 -m json.tool
```

**Response** (example):
```json
{
  "summary": "...",
  "technologies": ["Python", "urllib3", "..."],
  "structure": "...",
  "key_features": ["...", "..."],
  "architecture": "...",
  "getting_started": "...",
  "use_cases": ["...", "..."]
}
```

**Error Response**:
```json
{
  "detail": "Repository not found or is private"
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Interactive API Docs

FastAPI provides a built-in UI for exploring the API:
```
http://localhost:8000/docs
```

## Model Selection

### Chosen Model: Qwen/Qwen3-Coder-30B-A3B-Instruct (Nebius AI Studio)

**Why this model?**
- **Specialized for code**: Qwen3-Coder is specifically trained for code understanding and analysis
- **Strong reasoning**: Provides excellent analysis capabilities for diverse codebases
- **Cost-effective**: Available through Nebius AI Studio
- **Fast**: Optimized for quick responses while maintaining quality

The implementation also supports Anthropic Claude and OpenAI GPT-4 as alternatives.

## Repository Processing Strategy

### What We Include

1. **Priority Files** (always included):
   - README files (README.md, README.rst, etc.)
   - Package configuration (package.json, setup.py, pyproject.toml, Cargo.toml, etc.)
   - Build files (Dockerfile, Makefile, docker-compose.yml)
   - Architecture documentation (ARCHITECTURE.md, DESIGN.md)

2. **Source Files** (selectively):
   - Root-level source files (up to 10 files)
   - Main source files from primary directories (up to 15 files)
   - Prioritizes common languages: .py, .js, .ts, .java, .go, .rs, .c, .cpp

3. **Configuration Files** (limited):
   - Key config files like tsconfig.json, .eslintrc (up to 5 files)

4. **Directory Structure**:
   - Complete file tree (filtered, limited to 100 items)

### What We Skip

1. **Binary Files**: Images, videos, audio, compiled binaries, archives, fonts
2. **Generated/Dependency Files**: `node_modules/`, `__pycache__/`, lock files, build artifacts
3. **Environment/IDE Files**: `.vscode/`, `.idea/`, virtual environments

### Context Management

- **Individual file limit**: 5,000 characters (with truncation marker)
- **Total context limit**: ~100,000 characters across all files
- **Smart selection**: Priority files processed first
- **Graceful degradation**: System continues even if some files fail to fetch

## Project Structure

```
.
├── main.py              # FastAPI application, endpoints, and web UI
├── repo_analyzer.py     # GitHub API integration and file filtering
├── llm_client.py        # LLM API integration (multi-provider)
├── test_api.py          # API test suite
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Error Handling

| HTTP Status | Meaning |
|---|---|
| 400 Bad Request | Invalid GitHub URL format |
| 404 Not Found | Repository doesn't exist or is private |
| 500 Internal Server Error | API key not configured or unexpected error |
| 503 Service Unavailable | Network error or LLM API unavailable |

## Troubleshooting

**`LLM API key not configured`**
- Make sure `.env` exists and contains `NEBIUS_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`

**`rate limit exceeded`**
- Add a `GITHUB_TOKEN` to your `.env` file (see Setup)

**`Repository not found or is private`**
- Verify the URL is correct and the repository is public

**`Connection timeout`**
- Check your internet connection and try again

**Module not found errors**
- Make sure you activated your virtual environment: `source venv/bin/activate`

## License

This project is provided as-is for evaluation purposes.
