# Minimal Workflow Engine — Internship Assignment

This repo contains a small workflow/agent engine built with Python + FastAPI.
It implements a minimal graph engine that supports nodes (Python functions), a shared state, edges (including JSON-based conditional routing), looping, and a tool registry.

## What is included
- `app/engine.py` — core engine (updated to use safe JSON conditions)
- `app/tools.py` — example tools (detect_smells, compute_quality_score)
- `app/workflows.py` — sample Code-Review (Option A) workflow nodes
- `app/main.py` — FastAPI server exposing the required endpoints
- `samples/` — `good.py` and `bad.py` sample inputs
- `scripts/run_example.ps1` — PowerShell demo script
- `tests/` — pytest tests covering engine + endpoints
- `requirements.txt`

## Quick start (Windows PowerShell)

1. Create & activate virtualenv
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies
```powershell
pip install -r requirements.txt
```

3. Start server (from `app/` folder)
```powershell
cd app
uvicorn main:app --reload --port 8000
```

4. Health check
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

5. Run the sample workflow (PowerShell)
```powershell
$body = @{
  initial_state = @{
    code = Get-Content ../samples/bad.py -Raw
    threshold = 80
  }
  wait_for_completion = $true
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Uri "http://127.0.0.1:8000/graph/run" -Method Post -Body $body -ContentType "application/json" | Format-List
```

## What the engine supports
- Nodes: sync or async Python callables that accept `(state, tools)`.
- Shared state: a dictionary that flows through nodes.
- Edges: mapping node → next node; supports JSON-based conditional routing via condition lists.
- Looping: nodes can return a `(state, next_node)` tuple to loop back.
- Tool registry: `engine.register_tool(name, func)` to inject helper functions available to nodes.

## What I would improve with more time
- Persist graphs & runs in SQLite/Postgres instead of memory.
- Add WebSocket streaming for live logs.
- Add authentication and role-based node permissions.
- Improve the condition language or add a small DSL instead of JSON conditions.

## Notes for reviewers
- For simplicity, graph creation via `/graph/create` currently expects node names that map to pre-registered callables in `app/main.py`. This keeps the system safe and easy to reason about. See `main.py` for the registered nodes and example edges.
