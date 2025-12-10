# Minimal Workflow Engine — Internship Assignment

This repository contains a minimal workflow/agent engine built with Python + FastAPI.  
It implements a simplified graph engine that supports:

- Nodes (Python functions)
- Shared state flowing between nodes
- Edges (including JSON-based conditional routing)
- Looping logic
- A tool registry
- Optional WebSocket log streaming
- Pydantic-based state validation (StateModel)

The implementation corresponds to Option A: Code Review Mini-Agent from the assignment.

---

## Quick Start (Windows PowerShell)

Install dependencies:
```powershell
pip install -r requirements.txt
```

Start FastAPI server:
```powershell
cd app
uvicorn main:app --reload --port 8000
```

Health check:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Run sample Code Review workflow:
```powershell
cd ..
$body = @{
  initial_state = @{
    code = Get-Content .\samples\bad.py -Raw
    threshold = 80
  }
  wait_for_completion = $true
} | ConvertTo-Json -Depth 6

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/graph/run" `
    -Method Post `
    -Body $body `
    -ContentType "application/json" `
| Format-List
```

---

## State Model (Pydantic)

The workflow engine uses a Pydantic model (StateModel) to ensure the shared state is validated, structured, and predictable.

Definition (app/models.py):
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class StateModel(BaseModel):
    code: Optional[str] = Field("", description="Source code or text for analysis")
    threshold: Optional[int] = Field(80, description="Stopping threshold for quality score")

    # Populated by workflow nodes
    functions: List[str] = Field(default_factory=list)
    complexities: List[int] = Field(default_factory=list)
    complexity_avg: float = 0.0
    issues: int = 0
    tool_info: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    quality_score: float = 0.0
    iteration: int = 0

    class Config:
        extra = "allow"
```

How it works:

- `/graph/run` validates `initial_state`
- Missing fields are auto-filled
- Wrong types produce structured errors
- Engine internally uses dict for compatibility

Example run input:
```json
{
  "initial_state": {
    "code": "def a():\n  print('hello')",
    "threshold": 80
  },
  "wait_for_completion": true
}
```

---

## Workflow Engine Features

Nodes:
```python
(state: dict, tools: dict)
```

Shared State:
- Validated by Pydantic
- Enriched with defaults
- Converted to dict internally

Edges:
- Simple adjacency maps
- JSON-based conditional routing
- Nodes may override next step

Looping:
```python
return updated_state, "extract"
```
Allows “repeat until quality_score >= threshold”.

Tool registry:
```python
engine.register_tool("detect_smells", detect_smells)
```

---

## Tests

Run tests:
```powershell
python -m pytest -q
```

Tests cover:
- Health endpoint  
- Sync workflow run  
- Async workflow + polling  

All pass.

---

## Code Review Mini-Agent (Option A)

Workflow steps implemented:

1. Extract functions  
2. Compute complexity  
3. Detect issues  
4. Suggest improvements  
5. Loop until threshold reached  

Demonstrates:
- Branching  
- Looping  
- Tool usage  
- State transformation  
- Execution logs  

---

## What I Would Improve With More Time

- SQLite/Postgres persistence  
- Richer DSL for graph definitions  
- Parallel node execution  
- UI for workflow visualization  

---

## Notes for Reviewers

- Node names for `/graph/create` map to pre-registered functions in `main.py`
- A demo script (`scripts/run_example.ps1`) is included  
- README shows everything required to run & test the system  
