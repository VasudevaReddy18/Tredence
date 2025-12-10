# main.py - FastAPI app
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import asyncio

from .engine import GraphEngine
from . import workflows
from . import tools as mytools

app = FastAPI(title="Minimal Workflow Engine")

engine = GraphEngine()
engine.register_tool("detect_smells", mytools.detect_smells)
engine.register_tool("compute_quality_score", mytools.compute_quality_score)

nodes_spec = {
    "extract": workflows.extract_functions,
    "check_complexity": workflows.check_complexity,
    "detect_issues": workflows.detect_basic_issues,
    "suggest_improvements": workflows.suggest_improvements,
    "loop_decision": workflows.loop_decision,
}

edges = {
    "extract": "check_complexity",
    "check_complexity": "detect_issues",
    "detect_issues": "suggest_improvements",
    "suggest_improvements": "loop_decision",
    # loop_decision will return next hint or end
    "loop_decision": None
}

GRAPH_ID = engine.create_graph(nodes_spec, edges, start_node="extract")

class CreateGraphReq(BaseModel):
    nodes: Optional[Dict[str, str]] = None
    edges: Optional[Dict[str, Any]] = None
    start_node: Optional[str] = None

class RunReq(BaseModel):
    graph_id: Optional[str] = None
    initial_state: Dict[str, Any]
    wait_for_completion: Optional[bool] = False

@app.post("/graph/create")
async def create_graph(req: CreateGraphReq):
    if not req.nodes:
        raise HTTPException(status_code=400, detail="nodes spec required (name->registered node name)")
    nodes_map = {}
    for name, registered in req.nodes.items():
        if registered not in nodes_spec:
            raise HTTPException(status_code=400, detail=f"unknown registered node: {registered}")
        nodes_map[name] = nodes_spec[registered]
    edges = req.edges or {}
    start = req.start_node or list(nodes_map.keys())[0]
    graph_id = engine.create_graph(nodes_map, edges, start)
    return {"graph_id": graph_id}

@app.post("/graph/run")
async def run_graph(req: RunReq):
    graph_id = req.graph_id or GRAPH_ID
    if graph_id not in engine.graphs:
        raise HTTPException(status_code=404, detail="graph not found")
    run_id = engine.start_run(graph_id, req.initial_state)
    if req.wait_for_completion:
        timeout = 10.0
        waited = 0.0
        poll = 0.2
        while waited < timeout:
            run = engine.get_run_state(run_id)
            if run.status in ("finished", "failed"):
                return {"run_id": run_id, "status": run.status, "state": run.state, "log": run.log}
            await asyncio.sleep(poll)
            waited += poll
        return {"run_id": run_id, "status": "running", "message": "still running; poll /graph/state/{run_id}"}
    else:
        return {"run_id": run_id, "status": "started"}

@app.get("/graph/state/{run_id}")
async def get_state(run_id: str):
    run = engine.get_run_state(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "run_id": run.run_id,
        "graph_id": run.graph_id,
        "status": run.status,
        "current_node": run.current_node,
        "state": run.state,
        "log": run.log,
    }

@app.get("/health")
def health():
    return {"status": "ok", "sample_graph_id": GRAPH_ID}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

