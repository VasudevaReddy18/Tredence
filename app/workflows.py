# workflows.py
import asyncio
from typing import Dict, Any

async def extract_functions(state: Dict[str, Any], tools: Dict[str, Any]):
    code = state.get("code", "")
    funcs = []
    for chunk in code.split("\n\n"):
        if chunk.strip().startswith("def "):
            funcs.append(chunk.strip())
    if not funcs:
        funcs = [code]
    return {"functions": funcs}

def check_complexity(state: Dict[str, Any], tools: Dict[str, Any]):
    funcs = state.get("functions", [])
    complexities = [len(f.splitlines()) for f in funcs]
    state_update = {"complexities": complexities, "complexity_avg": sum(complexities)/len(complexities)}
    return state_update

def detect_basic_issues(state: Dict[str, Any], tools: Dict[str, Any]):
    funcs = state.get("functions", [])
    issues = 0
    for f in funcs:
        if "print(" in f and "logger" not in f:
            issues += 1
    tool = tools.get("detect_smells")
    tool_res = {}
    if tool:
        code = state.get("code", "")
        tool_res = tool(code)
    out = {"issues": issues + tool_res.get("issues", 0), "tool_info": tool_res}
    return out

def suggest_improvements(state: Dict[str, Any], tools: Dict[str, Any]):
    suggestions = []
    if state.get("issues", 0) > 0:
        suggestions.append("Replace prints with logger")
    if state.get("complexity_avg", 0) > 50:
        suggestions.append("Refactor large functions into smaller helpers")
    compute = tools.get("compute_quality_score")
    if compute:
        quality = compute({"issues": state.get("issues",0), "complexity": state.get("complexity_avg",0)})
    else:
        quality = 50.0
    return {"suggestions": suggestions, "quality_score": quality}

async def loop_decision(state: Dict[str, Any], tools: Dict[str, Any]):
    threshold = state.get("threshold", 80)
    quality = state.get("quality_score", 0)
    if quality >= threshold:
        return ({}, None)
    else:
        state.setdefault("iteration", 0)
        state["iteration"] += 1
        state["issues"] = max(0, state.get("issues", 0) - 1)
        compute = tools.get("compute_quality_score")
        if compute:
            state["quality_score"] = compute({"issues": state.get("issues",0), "complexity": state.get("complexity_avg",0)})
        if state["iteration"] > 5:
            return ({}, None)
        return (state, "suggest_improvements")
