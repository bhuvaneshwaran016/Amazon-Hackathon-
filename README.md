# TaskPilot AI — Hackathon starter

TaskPilot is a small productivity agent with:
- FastAPI web UI
- OpenAI Responses API function calling
- SQLite task persistence
- Separate MCP server over Streamable HTTP

## 1. Requirements
- Windows 10/11
- Python 3.11+ recommended
- OpenAI API key with API access/billing configured

## 2. Install (PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```
Put your key in `.env`. Never commit `.env` or paste the key into chat. If PowerShell blocks activation, use:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Run the web app
Terminal 1, from this directory:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app:app --reload --port 8000
```
Open http://127.0.0.1:8000

## 4. Run MCP server
Open a second PowerShell window in the same directory:
```powershell
.\.venv\Scripts\Activate.ps1
python mcp_server.py
```
The MCP endpoint is http://127.0.0.1:8001/mcp. It is local-only. For an external evaluator or remote host, deploy behind HTTPS and add authentication before exposing it publicly.

## 5. Test the demo
Try:
1. `Create a high-priority task to finish the hackathon submission tomorrow.`
2. `Show my open tasks and suggest a plan for today.`
3. `Mark task 1 complete.` (use an actual ID shown in the task board)
4. Refresh the browser and confirm tasks remain saved.

## Architecture notes
- The web agent uses OpenAI function calling to invoke the same Python task functions that the MCP server exposes.
- The MCP endpoint is independently callable by any compatible MCP host.
- To demonstrate the Alexa+ MCP route, connect an MCP-compatible host to the deployed HTTPS endpoint or show the local endpoint to a local MCP client. A localhost endpoint cannot be reached by a remote evaluator.
- The code is a prototype, not an official Alexa+ integration. Verify all event, account, submission, deployment, and judging requirements from the hackathon portal.

## Troubleshooting
- `OPENAI_API_KEY` missing: edit `.env`, then restart the web server.
- Model unavailable: change `OPENAI_MODEL` to a model enabled for your API account.
- `mcp.server.MCPServer` import error: your installed MCP SDK does not match this starter's SDK API. Check the official Python SDK docs for the current major version and adjust the server API accordingly; do not silently switch to SSE.
- Do not expose the development server to the public internet without authentication and HTTPS.
