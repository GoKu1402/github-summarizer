"""
GitHub Repository Summarizer API
FastAPI service that analyzes GitHub repositories and generates summaries using LLMs
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
import os
from typing import List
import logging
from dotenv import load_dotenv

from repo_analyzer import RepositoryAnalyzer
from llm_client import LLMClient

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GitHub Repository Summarizer",
    description="Analyzes GitHub repositories and generates intelligent summaries",
    version="1.0.0"
)


class SummarizeRequest(BaseModel):
    github_url: HttpUrl


class SummarizeResponse(BaseModel):
    summary: str
    technologies: List[str]
    structure: str
    key_features: List[str]
    architecture: str
    getting_started: str
    use_cases: List[str]


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Web UI"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>GitHub Repository Summarizer</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f6f8fa; color: #24292f; min-height: 100vh; }
    header { background: #24292f; color: white; padding: 16px 32px; display: flex; align-items: center; gap: 12px; }
    header svg { width: 32px; height: 32px; fill: white; }
    header h1 { font-size: 20px; font-weight: 600; }
    main { max-width: 860px; margin: 40px auto; padding: 0 24px; }
    .card { background: white; border: 1px solid #d0d7de; border-radius: 10px; padding: 28px; margin-bottom: 24px; }
    label { font-weight: 600; display: block; margin-bottom: 8px; }
    .input-row { display: flex; gap: 10px; }
    input[type=text] { flex: 1; padding: 10px 14px; border: 1px solid #d0d7de; border-radius: 6px; font-size: 15px; outline: none; }
    input[type=text]:focus { border-color: #0969da; box-shadow: 0 0 0 3px rgba(9,105,218,0.15); }
    button { padding: 10px 22px; background: #2da44e; color: white; border: none; border-radius: 6px; font-size: 15px; font-weight: 600; cursor: pointer; white-space: nowrap; }
    button:hover { background: #2c974b; }
    button:disabled { background: #94d3a2; cursor: not-allowed; }
    #status { margin-top: 14px; font-size: 14px; color: #57606a; display: none; }
    #error { margin-top: 14px; padding: 12px 16px; background: #fff0ee; border: 1px solid #ffcab1; border-radius: 6px; color: #cf222e; display: none; font-size: 14px; }
    #results { display: none; }
    .section { margin-bottom: 20px; }
    .section h3 { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: #57606a; margin-bottom: 10px; }
    .section p { line-height: 1.65; font-size: 15px; }
    .tags { display: flex; flex-wrap: wrap; gap: 6px; }
    .tag { background: #ddf4ff; color: #0550ae; border: 1px solid #b6e3ff; border-radius: 20px; padding: 3px 12px; font-size: 13px; font-weight: 500; }
    .list { list-style: none; padding: 0; }
    .list li { padding: 6px 0; padding-left: 18px; position: relative; font-size: 15px; line-height: 1.55; border-bottom: 1px solid #f0f0f0; }
    .list li:last-child { border-bottom: none; }
    .list li::before { content: "•"; position: absolute; left: 0; color: #2da44e; font-weight: bold; }
    .getting-started { background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 14px 18px; font-family: 'SFMono-Regular', Consolas, monospace; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
  </style>
</head>
<body>
  <header>
    <svg viewBox="0 0 16 16"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
    <h1>GitHub Repository Summarizer</h1>
  </header>
  <main>
    <div class="card">
      <label for="url">GitHub Repository URL</label>
      <div class="input-row">
        <input type="text" id="url" placeholder="https://github.com/owner/repo" />
        <button id="btn" onclick="summarize()">Summarize</button>
      </div>
      <div id="status">Analyzing repository, please wait...</div>
      <div id="error"></div>
    </div>

    <div id="results">
      <div class="card">
        <div class="section"><h3>Summary</h3><p id="r-summary"></p></div>
      </div>
      <div class="card">
        <div class="section"><h3>Technologies</h3><div id="r-tech" class="tags"></div></div>
      </div>
      <div class="card">
        <div class="section"><h3>Key Features</h3><ul id="r-features" class="list"></ul></div>
        <div class="section"><h3>Use Cases</h3><ul id="r-usecases" class="list"></ul></div>
      </div>
      <div class="card">
        <div class="section"><h3>Architecture</h3><p id="r-arch"></p></div>
        <div class="section"><h3>Project Structure</h3><p id="r-structure"></p></div>
      </div>
      <div class="card">
        <div class="section"><h3>Getting Started</h3><div id="r-start" class="getting-started"></div></div>
      </div>
    </div>
  </main>

  <script>
    async function summarize() {
      const url = document.getElementById('url').value.trim();
      const btn = document.getElementById('btn');
      const status = document.getElementById('status');
      const error = document.getElementById('error');
      const results = document.getElementById('results');

      if (!url) { showError('Please enter a GitHub URL.'); return; }

      btn.disabled = true;
      status.style.display = 'block';
      error.style.display = 'none';
      results.style.display = 'none';

      try {
        const res = await fetch('/summarize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ github_url: url })
        });
        const data = await res.json();
        if (!res.ok) { showError(data.detail || 'An error occurred.'); return; }

        document.getElementById('r-summary').textContent = data.summary;
        document.getElementById('r-arch').textContent = data.architecture;
        document.getElementById('r-structure').textContent = data.structure;
        document.getElementById('r-start').textContent = data.getting_started;

        document.getElementById('r-tech').innerHTML = data.technologies.map(t => `<span class="tag">${t}</span>`).join('');
        document.getElementById('r-features').innerHTML = data.key_features.map(f => `<li>${f}</li>`).join('');
        document.getElementById('r-usecases').innerHTML = data.use_cases.map(u => `<li>${u}</li>`).join('');

        results.style.display = 'block';
      } catch (e) {
        showError('Failed to reach the server.');
      } finally {
        btn.disabled = false;
        status.style.display = 'none';
      }
    }

    function showError(msg) {
      const el = document.getElementById('error');
      el.textContent = msg;
      el.style.display = 'block';
      document.getElementById('status').style.display = 'none';
      document.getElementById('btn').disabled = false;
    }

    document.getElementById('url').addEventListener('keydown', e => { if (e.key === 'Enter') summarize(); });
  </script>
</body>
</html>
"""


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_repository(request: SummarizeRequest):
    """
    Analyze a GitHub repository and return a summary
    
    Args:
        request: Contains the GitHub repository URL
        
    Returns:
        Summary with project description, technologies, and structure
    """
    try:
        github_url = str(request.github_url)
        logger.info(f"Processing repository: {github_url}")
        
        api_key = os.getenv("NEBIUS_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="LLM API key not configured. Please set NEBIUS_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY environment variable."
            )

        analyzer = RepositoryAnalyzer(github_url)
        llm_client = LLMClient(api_key)

        logger.info("Fetching repository contents...")
        repo_context = analyzer.analyze()

        logger.info("Generating summary with LLM...")
        result = llm_client.generate_summary(repo_context)
        
        logger.info("Summary generated successfully")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to connect to external service: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/health")
async def health_check():
    """Detailed health check"""
    api_key_configured = bool(
        os.getenv("NEBIUS_API_KEY") or 
        os.getenv("ANTHROPIC_API_KEY") or 
        os.getenv("OPENAI_API_KEY")
    )
    
    return {
        "status": "healthy",
        "api_key_configured": api_key_configured,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
